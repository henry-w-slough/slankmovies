from __future__ import annotations

import asyncio
import re
from typing import TypedDict

from playwright.async_api import (
	Browser,
	BrowserContext,
	Frame,
	Page,
	Playwright,
	Request,
	async_playwright,
)


class M3U8Data(TypedDict):
	url: str
	headers: dict[str, str]


# Activation is strictly ordered: an age/18+ confirmation is resolved first,
# then a cookie/consent banner, then the play control, and only these
# categories are ever clicked unless a genuine close control blocks the
# player. Generic "click anything that looks big" behaviour was removed so
# adverts and navigation links are not activated.
#
# "Accept" / "Agree" / "Continue" style wording is ambiguous on its own since
# both age gates and cookie banners use it, so the scanner also inspects each
# candidate's ancestor elements (class/id/aria-label) for age- or cookie-
# specific context before falling back to a default classification.
#
# The 18+ ask is always *agreed* to: wording that refuses the gate or leaves the
# site ("under 18", "exit", "no thanks", "disagree", ...) is listed in
# _AGE_DECLINE_KEYWORDS and skipped before classification, so it can never be
# clicked in any category, and among the age candidates that remain the
# affirmative ones (_AGE_AFFIRM_KEYWORDS) are ranked first (see _rank). The
# refusal check reads the same haystack classification does (label, class, id,
# aria-label, value, alt, data-*) plus the element's href/onclick and its
# wrappers' markers, because the refusal is often labelled with an icon or with
# "Enter" while pointing at /under18. A candidate matched solely by the
# ambiguous age wording is still clicked, because pressing "Enter" / "Verify" is
# what passes the gate.
#
# The tuples below are the single source of truth for the scan script: every
# name referenced as `keywords.<name>` inside _SCAN_SCRIPT must be supplied by
# _keyword_payload(), otherwise the frame evaluation throws and no candidate
# is ever found.
#
# Adverts are excluded twice over: elements and their ancestors carrying ad
# markers (class/id/data-action) are skipped, and iframes served by known ad
# networks are never scanned at all. Only the movie page itself is ever
# clicked; other windows the site opens (popunders, interstitials) are ignored
# for control activation, though their network traffic is still watched so a
# player opened in its own window can still be resolved.
_AGE_KEYWORDS = (
	"i am 18", "i'm 18", "i am over 18", "i'm over 18", "18 or older",
	"18 or over", "18 and over", "over 18", "are you 18", "18+",
	"yes, i am", "yes i am", "enter site", "adult content", "mature content",
	"verify your age", "verify my age", "confirm your age", "confirm my age",
	"date of birth", "birth date", "age verification", "age gate", "age-gate",
	"i am of legal age", "i am of age", "age of majority",
)
# Wording that positively answers an 18+ ask. The age step is only ever
# answered with these, so the gate is always passed rather than declined.
_AGE_AFFIRM_KEYWORDS = (
	"i am 18", "i'm 18", "i am over 18", "i'm over 18", "18 or older",
	"18 or over", "18 and over", "over 18", "yes, i am", "yes i am",
	"yes", "ok", "i agree", "agree", "accept", "enter", "enter site",
	"continue", "confirm", "verify", "submit", "i am of legal age", "i am of age",
)
# Wording that refuses the 18+ ask or takes the visitor away from the site.
# A candidate whose text reads like this is never clicked in any category, so
# an age gate is never answered by declining and activation never navigates the
# page away from the player. Matched with separators folded, so the "under-18"
# / "under18" / "/exit" spellings used in class names and URLs are covered by
# the same phrases as the displayed wording.
_AGE_DECLINE_KEYWORDS = (
	"under 18", "under18", "below 18", "below18", "not 18", "not18",
	"not over 18", "not yet 18", "younger than 18", "less than 18",
	"not old enough", "too young", "underage", "minor", "i am a minor",
	"i am not", "i'm not", "no i am not", "no, i am not",
	"no thanks", "not now", "no",
	"exit", "exit site", "leave", "leave site", "leave this site",
	"go back", "take me back", "take me away",
	"decline", "deny", "reject", "disagree", "do not agree", "don't agree",
	"sfw", "safe version", "safe mode", "browse safely", "safe browsing",
)
# The subset that is unambiguous enough to disqualify a *wrapper* as well as a
# control, and to be matched against class/id/href markers rather than only
# visible wording. Bare tokens such as "no" are deliberately absent: a control
# carrying a utility class like "no-scroll" must still be clickable, otherwise
# the gate could never be answered. The compound phrases at the end cover the
# very common "<option>-no" naming used when the refusal is labelled with an
# icon, because folding separators turns "age-gate-no" into "age gate no" and
# "age-option-no" into "age option no".
_AGE_DECLINE_CONTEXT_KEYWORDS = (
	"under 18", "under18", "below 18", "below18", "not 18", "not18",
	"not over 18", "not yet 18", "younger than 18", "less than 18",
	"not old enough", "too young", "underage", "i am a minor",
	"no thanks", "exit site", "leave site", "leave this site",
	"decline", "reject", "deny", "disagree", "do not agree", "don't agree",
	"sfw", "safe version", "safe mode", "browse safely",
	"gate no", "option no", "choice no", "variant no", "btn no",
	"button no", "verify no", "age no", "gate exit", "option exit",
	"gate decline", "option decline", "gate leave",
)
# Tokens that name a *refusal* option when they appear in a class/id/aria-label,
# together with the tokens that must directly precede them for the name to be
# the refusal's own container. This covers "age-option-no", "age-gate-exit" and
# also "age-no-enter" (where the refusal token is not the last word), because
# the check looks at every token position rather than only the final one.
_AGE_DECLINE_TOKEN_KEYWORDS = (
	"no", "exit", "leave", "decline", "reject", "deny", "disagree", "cancel",
	"back", "skip", "under",
)
_AGE_WRAPPER_KEYWORDS = (
	"age", "gate", "option", "choice", "variant", "verify", "verification",
	"confirm", "confirmation", "button", "btn", "link", "item", "entry",
	"answer",
)
# A refusal is also recognised *structurally* rather than only from the phrase
# list above, because gates word it in ways no list can enumerate ("under the
# age of 18", "below 18", "18 or under", "not yet an adult", "I'm not 18").
# Any wording that combines one of these negative words with one of the age
# words below is treated as a refusal, which is what stops an "Under 18"
# control being pressed when its label is spelt out at length. The two lists
# are matched against visible/labelling text only (never class or id), so a
# utility class such as "no-js" on the affirmative cannot disqualify it.
_AGE_DECLINE_NEAR_KEYWORDS = (
	"under", "below", "less", "younger", "young", "not", "no", "cannot",
	"can't", "won't", "without", "skip", "exit", "leave",
)
_AGE_TOKEN_KEYWORDS = (
	"18", "age", "adult", "years", "year", "old", "older", "born", "minor",
)
# Short wording such as "Enter" / "Verify" / "Confirm" is used by age gates
# but can also appear on cookie banners, so it is only classified from the
# surrounding container instead of being trusted outright.
_AGE_CONTEXT_KEYWORDS = (
	"enter", "verify", "confirm", "age", "submit",
)
# Explicit name for the 18+/age confirmation category, used by the activation
# order so the first step of the sequence reads clearly.
_CONFIRM_KEYWORDS = _AGE_KEYWORDS
_AGE_STRONG_KEYWORDS = (
	"18", "18+", "over 18", "age", "verify", "confirm", "birth", "born",
	"adult", "mature", "legal age", "majority",
)
_COOKIE_KEYWORDS = (
	"cookie", "cookies", "gdpr", "consent", "privacy policy",
	"we use cookies", "accept cookies", "allow cookies",
	"manage preferences", "cookie policy", "cookie settings",
	"cookie banner", "cookie notice", "cookie consent",
)
_GENERIC_ACCEPT_KEYWORDS = (
	"accept", "accept all", "agree", "i agree", "allow", "allow all",
	"got it", "ok", "continue", "yes",
)
_PLAY_KEYWORDS = (
	"play", "play now", "play video", "play movie", "click to play",
	"watch now", "▶", "►",
)
# "Close" controls are the last resort for a genuine popup. Refusal wording
# ("no thanks", "not now") used to live here, but it is now excluded from every
# category by _AGE_DECLINE_KEYWORDS so an 18+ ask can never be answered with a
# decline.
_DISMISS_KEYWORDS = (
	"close", "dismiss", "maybe later",
)

# Strict order for reaching the main video stream: any 18+/age ask is answered
# first, then the cookie/consent confirmation, and only then is the play
# control pressed. "dismiss" is a last-resort unblocker for a genuine close
# control (small elements only, see _collect_candidates).
_ACTIVATION_ORDER = ("confirm", "cookie", "play", "dismiss")

# Iframes served from known ad networks are skipped entirely, so a "Close" or
# "Play" button belonging to an interstitial can never be clicked by mistake.
# Ordinary (including same-origin / about:blank) frames are still scanned, and
# a frame is only treated as an advert when its URL clearly says so.
_AD_FRAME_HINTS = (
	"doubleclick", "googlesyndication", "googleads", "googletagmanager",
	"adservice", "adsystem", "adsbygoogle", "adserver", "ad_frame",
	"adframe", "/ads/", "/ad/", "advert", "popunder", "popads", "popcash",
	"exoclick", "juicyads", "trafficjunky", "trafficstars", "clickadu",
	"adsterra", "propellerads", "onclickads", "popmyads", "hilltopads",
	"revenuehits", "taboola", "outbrain", "mgid", "zergnet",
)

# Category -> keyword group used by the scan script for that category. The
# confirmation category is the 18+/age step that _ACTIVATION_ORDER runs first.
_KEYWORDS_BY_CATEGORY = {
	"confirm": _CONFIRM_KEYWORDS,
	"cookie": _COOKIE_KEYWORDS,
	"play": _PLAY_KEYWORDS,
	"dismiss": _DISMISS_KEYWORDS,
}


# Runs inside each frame. It only inspects interactive elements (and elements
# whose class/id clearly references a player/confirmation), excludes adverts,
# off-site links and new-tab links, then classifies the survivors.
_SCAN_SCRIPT = r"""
(keywords) => {
    const normalize = (value) => (value || '').replace(/\s+/g, ' ').trim().toLowerCase();

    // Defensive accessor. A keyword list the payload forgot to supply must
    // degrade to "matches nothing" instead of throwing: a throw here aborts the
    // whole frame scan, which is indistinguishable from a page with no controls
    // and silently disables every confirmation step.
    const listOf = (value) => (Array.isArray(value) ? value : []);

    const escapeRegExp = (value) => value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

    // Wording the visitor actually sees, without class/id/attribute noise, so a
    // refusal is recognised even when its container is named like an accept
    // control (e.g. <button class="age-gate-no">No</button>).
    const visibleText = (el) => normalize(el.innerText || el.textContent || '');

    // Every marker a refusal could hide in: the same haystack classification
    // uses (describe) plus the element's own URL and handler. Age gates
    // routinely label the refusal with an icon, with "Enter", or with a class
    // like "age-no-enter" while pointing it at /under18, so the filter and the
    // classifier must read from the same text or they disagree about which
    // control is a refusal.
    const markerText = (el) => normalize([
        describe(el),
        el.getAttribute('href'),
        el.getAttribute('onclick'),
        el.getAttribute('formaction'),
    ].filter(Boolean).join(' '));

    // Wrappers whose *name* marks them as the refusal's own container, e.g.
    // "age-option-no", "age-gate-exit" or "age-no-enter" (the refusal token is
    // not necessarily the last one). Each class/id/aria-label string is
    // examined on its own, so a shared modal carrying a utility class such as
    // "no-scroll" next to "age-gate" is not mistaken for the refusal's wrapper
    // -- that mistake would disqualify the affirmative along with the refusal
    // and leave the gate unanswerable.
    const isRefusalWrapper = (node) => {
        const markers = [
            typeof node.className === 'string' ? node.className : '',
            node.id,
            node.getAttribute('aria-label'),
            node.getAttribute('data-testid'),
        ].filter(Boolean);

        return markers.some((marker) => {
            const tokens = normalize(marker)
                .replace(/[-_.]+/g, ' ')
                .split(/\s+/).filter(Boolean);

            for (let i = 1; i < tokens.length; i += 1) {
                if (listOf(keywords.ageDeclineToken).includes(tokens[i]) &&
                    listOf(keywords.ageWrapper).includes(tokens[i - 1])) {
                    return true;
                }
            }
            return false;
        });
    };

    // Markers on the wrapping elements, so a control nested inside a refusal
    // option (<div class="age-option-no">, <a href="/under18">) is recognised
    // even though the control's own label looks like an accept control. The
    // wrapper's *text* is deliberately not used: both options often share one
    // container, and matching its text would disqualify the affirmative too.
    const ancestorIsRefusal = (el) => {
        let node = el.parentElement;
        let depth = 0;
        while (node && depth < 4) {
            const markers = normalize([
                typeof node.className === 'string' ? node.className : '',
                node.id,
                node.getAttribute('aria-label'),
                node.getAttribute('href'),
                node.getAttribute('onclick'),
                node.getAttribute('data-action'),
            ].filter(Boolean).join(' '));

            if (matchesWord(markers, keywords.ageDeclineStrong)) return true;
            if (isRefusalWrapper(node)) return true;

            node = node.parentElement;
            depth += 1;
        }
        return false;
    };

    // A refusal must never be clicked, whatever category it would fall into.
    // Three independent checks, because a refusal hides its nature in
    // different places: the displayed wording, the way it is worded, and the
    // markers on the element and its wrappers.
    const isDecline = (el) =>
        matchesWord(markerText(el), keywords.ageDecline) ||
        refusesByWording(el) ||
        ancestorIsRefusal(el);

    const matchesWord = (text, words) => {
        // Separators are folded so marker-style wording ("under-18",
        // "under18", "no_thanks", "/exit") matches the same phrase list as
        // display text ("under 18").
        const fold = (value) => (value || '').replace(/[-_.]+/g, ' ');
        const hay = fold(text);
        return listOf(words).some((word) => {
            if (!word) return false;
            const needle = fold(word);
            if (!needle) return false;
            const pattern = new RegExp(
                '(^|[^a-z0-9])' + escapeRegExp(needle) + '([^a-z0-9]|$)'
            );
            return pattern.test(hay);
        });
    };

    // What the visitor sees or a screen reader announces. Class and id are
    // deliberately excluded: a shared utility class such as "no-js" or
    // "no-scroll" must not make the affirmative look like a refusal.
    const labelText = (el) => normalize([
        el.innerText,
        el.textContent,
        el.getAttribute('aria-label'),
        el.getAttribute('title'),
        el.getAttribute('alt'),
        el.getAttribute('value'),
    ].filter(Boolean).join(' '));

    // Separators folded, surrounding punctuation stripped, so "(18+)" and
    // "18+" both yield the token "18" while "1080p" stays "1080p" and cannot
    // be mistaken for "18".
    const tokensOf = (value) =>
        normalize(value)
            .replace(/[-_.]+/g, ' ')
            .split(/\s+/)
            .map((token) => token.replace(/^[^a-z0-9]+|[^a-z0-9]+$/g, ''))
            .filter(Boolean);

    const hasAny = (tokens, words) =>
        listOf(words).some((word) => tokens.includes(word));

    // Worded refusal: a negative word next to an age word. This catches the
    // long spellings no phrase list covers ("under the age of 18", "18 or
    // under", "not yet an adult"), while an affirmative such as "I am 18 or
    // older" contains neither word from the negative list.
    const refusesByWording = (el) => {
        const tokens = tokensOf(labelText(el));
        return hasAny(tokens, keywords.ageDeclineNear) &&
            hasAny(tokens, keywords.ageTokens);
    };

    const isVisible = (el) => {
        const rect = el.getBoundingClientRect();
        if (rect.width < 4 || rect.height < 4) return false;
        const style = window.getComputedStyle(el);
        if (style.visibility === 'hidden' || style.display === 'none') return false;
        if (parseFloat(style.opacity || '1') < 0.05) return false;
        return true;
    };

    const describe = (el) => normalize([
        el.innerText,
        el.textContent,
        el.getAttribute('aria-label'),
        el.getAttribute('title'),
        el.getAttribute('value'),
        el.getAttribute('alt'),
        el.getAttribute('name'),
        typeof el.className === 'string' ? el.className : '',
        el.id,
        el.getAttribute('data-action'),
        el.getAttribute('data-testid'),
    ].filter(Boolean).join(' '));

    const isInteractive = (el) => {
        const tag = el.tagName.toLowerCase();
        if (['button', 'a', 'input', 'summary', 'label'].includes(tag)) return true;
        const role = el.getAttribute('role');
        if (role === 'button' || role === 'link') return true;
        if (el.hasAttribute('onclick')) return true;
        return window.getComputedStyle(el).cursor === 'pointer';
    };

    const classTokensOf = (el) =>
        (typeof el.className === 'string' ? el.className : '')
            .toLowerCase().split(/\s+/).filter(Boolean);

    // The element plus a few ancestors. Used so that a control nested inside a
    // wrapper (an <a>, an ad container) inherits the wrapper's properties
    // instead of only being judged on its own attributes.
    const selfAndAncestors = (el, depth) => {
        const chain = [];
        let node = el;
        let level = 0;
        while (node && level < depth) {
            chain.push(node);
            node = node.parentElement;
            level += 1;
        }
        return chain;
    };

    const adTokenPattern = (t) =>
        t === 'ad' || t === 'ads' ||
        t.startsWith('ad-') || t.startsWith('ad_') ||
        t.endsWith('-ad') || t.endsWith('_ad') ||
        t.includes('advert') || t.includes('sponsor') ||
        t.includes('adsbygoogle') || t.includes('popunder') ||
        t.includes('exoclick') || t.includes('juicyads') ||
        t.includes('trafficjunky');

    const hasAdMarker = (el) => {
        const tokens = classTokensOf(el);
        if (tokens.some(adTokenPattern)) return true;

        const hay = tokens.join(' ') + ' ' +
            normalize(el.id) + ' ' + normalize(el.getAttribute('data-action'));
        return hay.includes('advert') || hay.includes('sponsor') ||
            hay.includes('adsbygoogle');
    };

    // Adverts are recognised from the element *and* its ancestors, so a "Play"
    // button sitting inside <div class="ad-overlay"> is treated as part of the
    // advert instead of as the movie's play control.
    const looksLikeAd = (el) =>
        selfAndAncestors(el, 4).some(hasAdMarker);

    const anchorIsForeign = (el) => {
        if (el.tagName.toLowerCase() !== 'a') return false;
        const href = (el.getAttribute('href') || '').trim();
        if (!href) return false;
        const lower = href.toLowerCase();
        if (lower.startsWith('#') || lower.startsWith('javascript:')) return false;
        try {
            const url = new URL(href, location.href);
            if (url.protocol !== 'http:' && url.protocol !== 'https:') return false;
            return url.hostname !== location.hostname;
        } catch (e) {
            return false;
        }
    };

    // A button wrapped in an off-site / new-tab <a> is a popunder trigger, so
    // ancestor links are inspected too rather than just the control itself.
    const isForeignLink = (el) =>
        selfAndAncestors(el, 4).some(anchorIsForeign);

    const opensNewTab = (el) =>
        selfAndAncestors(el, 4).some(
            (node) => (node.getAttribute('target') || '').toLowerCase() === '_blank'
        );

    // Play controls are ranked with this: a control inside the player container
    // starts the main video stream, whereas a "play" link on a related-video
    // thumbnail navigates away from it.
    const playerMarkers = [
        'player', 'video-js', 'vjs', 'jwplayer', 'flowplayer', 'plyr',
        'media-player', 'hls', 'stream',
    ];

    const insidePlayer = (el) => {
        let node = el.parentElement;
        let depth = 0;
        while (node && depth < 5) {
            const hay = classTokensOf(node).join(' ') + ' ' + normalize(node.id);
            if (playerMarkers.some((marker) => hay.includes(marker))) return true;
            node = node.parentElement;
            depth += 1;
        }
        return false;
    };

    // Generic wording like "Accept" / "Agree" / "Continue" is used by both
    // age gates and cookie banners, so climb a few ancestors and look at
    // their class/id/aria-label/role for context clues before guessing.
    const ancestorContext = (el) => {
        let node = el.parentElement;
        let depth = 0;
        const parts = [];
        while (node && depth < 6) {
            parts.push(
                normalize(node.className && typeof node.className === 'string' ? node.className : ''),
                normalize(node.id),
                normalize(node.getAttribute('aria-label')),
                normalize(node.getAttribute('data-testid')),
                normalize(node.getAttribute('role'))
            );
            node = node.parentElement;
            depth += 1;
        }
        return parts.filter(Boolean).join(' ');
    };

    // Classification decides *when* an element is clicked (see
    // _ACTIVATION_ORDER), so the category drives the strict
    // 18+ -> cookie -> play sequence rather than just filtering.
    const classify = (el, text) => {
        const context = ancestorContext(el);

        // Explicit age wording: "I am 18", "18 or older", "age gate", ...
        if (matchesWord(text, keywords.age)) return 'confirm';
        // Explicit cookie wording: "Accept cookies", "GDPR", "consent", ...
        if (matchesWord(text, keywords.cookie)) return 'cookie';

        // Short age wording ("Enter", "Verify", "Confirm", "Age"). A cookie
        // banner reusing that wording is recognised through its container.
        if (matchesWord(text, keywords.ageContext)) {
            return matchesWord(context, keywords.cookie) ? 'cookie' : 'confirm';
        }

        // Ambiguous "Accept" / "Agree" / "Continue" wording is resolved from
        // the surrounding container. Without usable context the safest
        // assumption is a consent banner, which is only ever clicked once the
        // age gate has already been answered.
        if (matchesWord(text, keywords.genericAccept)) {
            if (matchesWord(context, keywords.age) ||
                matchesWord(context, keywords.ageContext)) return 'confirm';
            return 'cookie';
        }

        if (matchesWord(text, keywords.play)) return 'play';
        if (matchesWord(text, keywords.dismiss)) return 'dismiss';
        return null;
    };

    document.querySelectorAll('[data-slank-candidate]').forEach((el) =>
        el.removeAttribute('data-slank-candidate'));

    const nodes = document.querySelectorAll(
        'button, a, input, summary, [role="button"], [role="link"], [onclick], ' +
        '[class*="play" i], [id*="play" i], [aria-label*="play" i], [title*="play" i], ' +
        '[data-action*="play" i], [data-testid*="play" i], ' +
        '[class*="confirm" i], [class*="verify" i], [class*="age-gate" i], ' +
        '[class*="agegate" i], [id*="age-gate" i], [id*="agegate" i], ' +
        '[class*="age-verif" i], [id*="age-verif" i], [aria-label*="age" i], ' +
        '[aria-label*="18" i], [title*="18" i], [value*="18" i], ' +
        '[data-testid*="age" i], [data-action*="age" i], ' +
        '[class*="cookie" i], [id*="cookie" i], [class*="consent" i], ' +
        '[id*="consent" i], [class*="gdpr" i], [id*="gdpr" i]'
    );

    const results = [];
    const vw = window.innerWidth || 1;
    const vh = window.innerHeight || 1;
    let index = 0;

    for (const el of nodes) {
        if (el === document.body || el === document.documentElement) continue;
        if (!isVisible(el)) continue;
        if (looksLikeAd(el)) continue;
        if (isForeignLink(el) || opensNewTab(el)) continue;
        if (!isInteractive(el)) continue;

        const text = describe(el);
        if (!text || text.length > 80) continue;

        // Never answer an 18+ ask with a refusal, and never follow a control
        // that leaves the site. Checked against every marker the element and
        // its wrappers carry (label, class, id, URL, handler) before
        // classification, so a decline cannot be picked up by the "dismiss",
        // "cookie", "confirm" or "play" categories either.
        if (isDecline(el)) continue;

        // classify needs the element as well as the text so ambiguous wording
        // can be resolved from the surrounding container.
        const category = classify(el, text);
        if (!category) continue;

        const rect = el.getBoundingClientRect();
        const key = 'sc' + (index++);
        el.setAttribute('data-slank-candidate', key);
        results.push({
            key,
            category,
            text: text.slice(0, 80),
            ratio: (rect.width * rect.height) / (vw * vh),
            ageStrong: matchesWord(text, keywords.ageStrong),
            agrees: matchesWord(text, keywords.ageAffirm),
            inPlayer: insidePlayer(el),
            tag: el.tagName.toLowerCase(),
        });
    }

    return results;
}
"""

def _keyword_payload() -> dict[str, list[str]]:
	"""Keyword lists handed to _SCAN_SCRIPT, keyed by the names it reads.

	Every name the script references as ``keywords.<name>`` has to appear here.
	The script receives nothing else, so an omitted name raises inside the frame
	and is swallowed by the caller, leaving the scan silently matching nothing
	at all. ``_check_scan_keywords`` below turns that into a loud import error.
	"""
	payload = {
		name: list(keywords)
		for name, keywords in _KEYWORDS_BY_CATEGORY.items()
	}
	payload.update(
		age=list(_AGE_KEYWORDS),
		ageContext=list(_AGE_CONTEXT_KEYWORDS),
		ageStrong=list(_AGE_STRONG_KEYWORDS),
		ageAffirm=list(_AGE_AFFIRM_KEYWORDS),
		ageDecline=list(_AGE_DECLINE_KEYWORDS),
		ageDeclineNear=list(_AGE_DECLINE_NEAR_KEYWORDS),
		ageTokens=list(_AGE_TOKEN_KEYWORDS),
		ageDeclineStrong=list(_AGE_DECLINE_CONTEXT_KEYWORDS),
		ageDeclineToken=list(_AGE_DECLINE_TOKEN_KEYWORDS),
		ageWrapper=list(_AGE_WRAPPER_KEYWORDS),
		genericAccept=list(_GENERIC_ACCEPT_KEYWORDS),
	)
	return payload


_KEYWORD_REFERENCE_RE = re.compile(r"keywords\.([A-Za-z][A-Za-z0-9]*)")


def _missing_scan_keywords() -> list[str]:
	"""Names _SCAN_SCRIPT reads that the payload does not provide."""
	return sorted(
		set(_KEYWORD_REFERENCE_RE.findall(_SCAN_SCRIPT)) - set(_keyword_payload())
	)


def _check_scan_keywords() -> None:
	"""Fail loudly when the scan script and the payload have drifted apart."""
	missing = _missing_scan_keywords()
	if missing:
		raise RuntimeError(
			"_SCAN_SCRIPT reads keyword lists that _keyword_payload() does not "
			f"provide: {missing}. Every `keywords.<name>` must have a matching "
			"key, otherwise the frame evaluation throws and no confirmation "
			"step can ever be clicked."
		)


_check_scan_keywords()


_NUDGE_VIDEO_SCRIPT = r"""
() => {
    const videos = [...document.querySelectorAll('video')];
    const video = videos.find((item) => !item.classList.contains('gifVideo'));
    if (!video) return;
    video.muted = true;
    video.setAttribute('playsinline', '');
    const attempt = video.play();
    if (attempt && typeof attempt.catch === 'function') attempt.catch(() => {});
}
"""


class WebScraper:
	"""Resolve an HLS playlist requested by a movie page in a real browser."""

	def __init__(self, headless: bool = True) -> None:
		self.headless = headless
		self.playwright: Playwright | None = None
		self.browser: Browser | None = None
		self.context: BrowserContext | None = None
		self.pages: set[Page] = set()
		self.playlist_requests: list[Request] = []


	async def start(self) -> None:
		self.playwright = await async_playwright().start()

		# The default headless=True launch uses the stripped-down headless
		# shell binary, which is trivially detected by the bot checks these
		# sites run before serving the player: navigator.userAgent reports
		# "HeadlessChrome", navigator.plugins is empty, pdfViewerEnabled is
		# false, window.chrome is undefined and WebGL falls back to a
		# SwiftShader renderer instead of the real GPU. In that state the
		# player never starts, so no m3u8 request is ever observed. The full
		# Chromium binary in its new headless mode ("chromium" channel)
		# matches the headed fingerprint for all of those except the UA
		# string, which is normalised below.
		if self.headless:
			self.browser = await self.playwright.chromium.launch(
				headless=True, channel="chromium"
			)
		else:
			self.browser = await self.playwright.chromium.launch(headless=False)

		if self.headless:
			# Read the headless UA from the browser itself so it stays in
			# sync with the installed version, then drop the HeadlessChrome
			# marker. This also fixes the headers resolve_m3u8() replays
			# through RequestHandler, which would otherwise carry the
			# HeadlessChrome agent onto every segment request too.
			probe = await self.browser.new_context()
			try:
				page = await probe.new_page()
				raw_ua = await page.evaluate("navigator.userAgent")
			finally:
				await probe.close()

			self.context = await self.browser.new_context(
				user_agent=raw_ua.replace("HeadlessChrome", "Chrome")
			)
			# Chromium reports navigator.webdriver as true under automation
			# even when headed; a normal session reports false.
			await self.context.add_init_script(
				"Object.defineProperty(navigator, 'webdriver', {get: () => false});"
			)
		else:
			self.context = await self.browser.new_context()

		self.context.on("page", self._register_page)



	async def close(self) -> None:
		if self.browser is not None:
			await self.browser.close()
			self.browser = None

		if self.playwright is not None:
			await self.playwright.stop()
			self.playwright = None

		self.context = None
		self.pages.clear()


	async def resolve_m3u8(self, movie_url: str, timeout: float = 30.0) -> M3U8Data:
		"""Load a movie page, start playback, and return the HLS request details."""
		if self.context is None:
			raise RuntimeError("Call start() before resolve_m3u8().")

		self.playlist_requests.clear()
		page = await self.context.new_page()
		self._register_page(page)

		try:
			await page.goto(
				movie_url,
				wait_until="domcontentloaded",
				timeout=int(timeout * 1000),
			)

			await self._activate_playback(page, timeout)

			if not self.playlist_requests:
				raise TimeoutError(
					f"No m3u8 request was observed for '{movie_url}'. "
					"A site verification may require user interaction."
				)

			request = self._select_playlist_request()
			return {
				"url": request.url,
				"headers": dict(request.headers),
			}
		finally:
			await page.close()
			self.pages.discard(page)


	def _register_page(self, page: Page) -> None:
		if page in self.pages:
			return

		self.pages.add(page)
		page.on("request", self._capture_request)


	def _capture_request(self, request: Request) -> None:
		url = request.url.lower()
		if ".m3u8" in url or "/hls/" in url or "/manifest" in url:
			self.playlist_requests.append(request)


	def _select_playlist_request(self) -> Request:
		def score(request: Request) -> int:
			url = request.url.lower()
			return sum(
				marker in url
				for marker in ("master", "playlist", "manifest")
			)

		return max(self.playlist_requests, key=score)


	async def _activate_playback(self, page: Page, timeout: float) -> None:
		"""Confirm in strict order: 18+ ask, cookie confirmation, then play.

		Every pass over _ACTIVATION_ORDER stops after a single click and then
		restarts from the first category, so an age gate is always answered
		before a cookie banner is accepted and the play control for the main
		stream is only pressed once neither is still blocking the player.

		Controls are sought on the movie page only: ad iframes are skipped and
		every other window the site opened is ignored, so an unrelated popup or
		interstitial is never clicked."""
		deadline = asyncio.get_running_loop().time() + timeout
		clicked: set[str] = set()

		while not self.playlist_requests:
			if asyncio.get_running_loop().time() >= deadline:
				return

			progressed = False
			for category in _ACTIVATION_ORDER:
				if self.playlist_requests:
					return

				if await self._click_category(category, clicked, page):
					progressed = True
					# Restart the sequence so the precedence stays strict.
					break

			await self._nudge_video(page)

			if self.playlist_requests:
				return

			await asyncio.sleep(0.4 if progressed else 0.6)


	def _keyword_payload(self) -> dict[str, list[str]]:
		return _keyword_payload()


	async def _click_category(
		self, category: str, clicked: set[str], page: Page
	) -> bool:
		"""Click the single best unclicked candidate for one category.

		Candidates come from the movie page only, so a control belonging to an
		advert or to an unrelated popup window the site opened is never
		activated."""
		candidates = await self._collect_candidates(category, clicked, page)
		if not candidates:
			return False

		candidates.sort(key=self._rank)
		best = candidates[0]
		clicked.add(best["signature"])

		locator = best["frame"].locator(
			f'[data-slank-candidate="{best["key"]}"]'
		)
		await self._click_locator(locator)
		return True


	async def _collect_candidates(
		self, category: str, clicked: set[str], page: Page
	) -> list[dict]:
		"""Collect clickable candidates for one category from the movie page.

		Only the movie page is scanned, never any other window the site opened,
		so a control belonging to an advert or an unrelated popup is never
		activated. Frames inside the page are still scanned (including
		third-party consent frames), while known ad-network iframes are skipped.
		Network traffic from other windows is still observed by
		``_capture_request``, so a player the site opens in its own window can
		still be resolved."""
		payload = self._keyword_payload()

		if page.is_closed():
			self.pages.discard(page)
			return []

		return await self._scan_page(page, category, payload, clicked)


	async def _scan_page(
		self,
		open_page: Page,
		category: str,
		payload: dict[str, list[str]],
		clicked: set[str],
	) -> list[dict]:
		"""Scan every non-ad frame of one page for this category."""
		results: list[dict] = []

		for frame in open_page.frames:
			if self._frame_is_ad(frame):
				continue

			try:
				raw = await frame.evaluate(_SCAN_SCRIPT, payload)
			except Exception:
				continue

			for candidate in raw:
				if candidate.get("category") != category:
					continue

				signature = (
					f"{id(frame)}|{category}|{candidate['text']}"
				)
				if signature in clicked:
					continue

				# Only accept a "close" control if it is a small element,
				# never a big banner that could be an advert.
				if category == "dismiss" and candidate.get("ratio", 1.0) > 0.25:
					continue

				candidate["frame"] = frame
				candidate["signature"] = signature
				results.append(candidate)

		return results


	@staticmethod
	def _frame_is_ad(frame: Frame) -> bool:
		"""True when a frame belongs to a known ad network."""
		hay = f"{frame.url} {frame.name}".lower()
		return any(hint in hay for hint in _AD_FRAME_HINTS)


	@staticmethod
	def _rank(candidate: dict) -> tuple[int, int, float]:
		# Age gates are ranked so the affirmative answer ("I am 18+", "Agree",
		# "Enter") always beats anything ambiguous: the 18+ ask is agreed to,
		# never declined. Any remaining candidate still passes the gate.
		if candidate.get("category") == "confirm":
			affirm = 0 if candidate.get("agrees") else 1
			strong = 0 if candidate.get("ageStrong") else 1
			return (affirm, strong, -candidate.get("ratio", 0.0))

		# Play controls inside a player container are preferred so the main
		# stream starts instead of a thumbnail/preview control. The rest prefer
		# the most prominent (largest) element.
		player = 0 if candidate.get("inPlayer") else 1
		strong = 0 if candidate.get("ageStrong") else 1
		return (player, strong, -candidate.get("ratio", 0.0))


	async def _click_locator(self, locator) -> bool:
		"""Activate an element without ever clicking its neighbour by accident.

		The first attempt is an ordinary Playwright click, which verifies that
		the chosen element is really the one receiving the event at the click
		point. ``force=True`` is deliberately *not* used: it skips that check
		and dispatches the press at the element's centre coordinates, so when
		the affirmative answer is positioned under the refusal -- stacked gate
		options, a "Under 18" button sitting over a "Enter" panel -- the press
		lands on the refusal even though it was never selected as a candidate
		and had already been filtered out.

		The remaining attempts dispatch the event on the chosen element itself,
		with no coordinates involved, so a control that a blocker would normally
		intercept can still be activated with no chance of hitting another
		element."""
		try:
			await locator.first.click(timeout=1500)
			return True
		except Exception:
			pass

		try:
			await locator.first.evaluate(
				"el => { el.scrollIntoView({block: 'center'}); el.click(); }"
			)
			return True
		except Exception:
			pass

		try:
			await locator.first.evaluate(
				"""
				el => {
					el.scrollIntoView({block: 'center'});
					for (const type of ['mousedown', 'mouseup', 'click']) {
						el.dispatchEvent(new MouseEvent(type, {bubbles: true, cancelable: true}));
					}
				}
				"""
			)
			return True
		except Exception:
			return False


	async def _nudge_video(self, page: Page) -> None:
		"""Best-effort attempt to start native <video> playback on the movie page.

		Scoped to the movie page on purpose: calling play() on a video inside an
		advert iframe or an unrelated popup window would start third-party
		playback instead of the stream we are resolving."""
		if page.is_closed():
			return

		for frame in page.frames:
			if self._frame_is_ad(frame):
				continue

			try:
				await frame.evaluate(_NUDGE_VIDEO_SCRIPT)
			except Exception:
				continue