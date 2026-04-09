from ..Models import Movie
from ..Utility import ChunkParser, ChunkReader

class MovieRepository:


    def __init__(self) -> None:
        """Handles all logic for Movie data and Movie storing."""
        #holds all Movie instances and their ids
        self.all_movies: dict[str, Movie.Movie] = {
            
        }


    def add_movie(self, movie:Movie.Movie) -> None:
        """Adds a new movie to the Repository movie dict with the given attributes"""
        self.all_movies[movie.id] = movie

        print(self.all_movies)