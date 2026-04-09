from ..Models import Movie

from ..Utility import ChunkParser
from ..Utility import ChunkCombiner

from .. import config

class MovieRepository:


    def __init__(self) -> None:
        """Handles all logic for Movie data and Movie storing."""
        #holds all Movie instances and their ids
        self.all_movies: dict[str, Movie.Movie] = {
            
        }


    def add_movie(self, movie:Movie.Movie, src:str) -> None:
        """Adds a new movie to the Repository movie dict with the given attributes"""
        self.all_movies[movie.id] = movie   
        ChunkParser.file_to_chunks(movie, src, config.DEFAULT_READ_SIZE)


    def get_movie_by_id(self, id:str) -> Movie.Movie:
        return self.all_movies[id]


    def get_movie_by_name(self, name:str) -> Movie.Movie:
        for movie in self.all_movies.values():
            if movie.name == name:
                return movie
        print("WARNING: MovieRepository: get_movie_by_name: No movie of name {name} was found.")
        return Movie.Movie(-1, "")
   


        