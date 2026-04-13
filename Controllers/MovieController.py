from ..Services import MovieService
from ..Models import Movie


class MovieController:


    def __init__(self) -> None:
        """Handles all user-directed Movie actions."""
        self.movie_service = MovieService.MovieService()


    def add_movie(self, name:str, src:str) -> None:
        self.movie_service.add_movie(name, src)


    def get_movie_by_id(self, id:str) -> Movie.Movie:
        return self.movie_service.get_movie_by_id(id)


    def get_movie_by_name(self, name:str) -> Movie.Movie:
        return self.movie_service.get_movie_by_name(name)


    def copy_movie(self, movie:Movie.Movie, new_dir:str) -> None:
        self.movie_service.copy_movie(movie, new_dir)
        





