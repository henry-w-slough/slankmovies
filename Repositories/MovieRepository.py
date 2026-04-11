from ..Models import Movie

from ..Utility import ChunkParser
from ..Utility import ChunkCombiner

from .. import config

import os
import uuid

class MovieRepository:


    def __init__(self) -> None:
        """Handles all logic for Movie data and Movie storing."""
        #holds all Movie instances and their directories
        self.all_movies: dict[str, Movie.Movie] = {
            
        }


    def add_movie(self, movie:Movie.Movie, src:str) -> None:
        """Adds a new movie to the Repository movie dict with the given attributes"""
        self.all_movies[os.path.join(config.MOVIES_DIR, movie.name)] = movie   
        ChunkParser.file_to_chunks(movie, src, config.DEFAULT_READ_SIZE)


    def get_movie_by_id(self, id:str) -> Movie.Movie | None:
        """Returns the Movie corresponding to the given Id. If it's not found, None is returned."""
        return self.all_movies.get(id, None)


    def get_movie_by_name(self, name:str) -> Movie.Movie | None:
        """Returns the Movie corresponding to the given Name. If it's not found, None is returned."""
        for movie in self.all_movies.values():
            if movie.name == name:
                return movie
        return None


    def get_movie_directory(self, movie:Movie.Movie) -> str | None:
        """Returns the directory (string) of the given Movie. If the Movie is not found, None is returned."""
        for dir, m in self.all_movies.items():
            if movie == m:
                return dir
        return None


    def copy_movie(self, movie:Movie.Movie, new_dir:str) -> None:
        """Copies the given Movie's data into another directory."""
        movie_dir = self.get_movie_directory(movie)
        if movie_dir:
            chunks_dir = os.path.join(movie_dir, config.MOVIE_DATA_DIR)
            ChunkCombiner.chunks_to_file(movie, chunks_dir, new_dir)
            