from ..Models import Movie

from ..Utility import ChunkParser
from ..Utility import ChunkCombiner

from .. import config

import os
import uuid

class MovieRepository:


    def __init__(self) -> None:
        """Handles all logic for Movie data and Movie storing."""
        #holds all Movie instances and their ids
        self.all_movies: dict[str, Movie.Movie] = {
            
        }


    def add_movie(self, movie:Movie.Movie, src:str) -> None:
        """Adds a new movie to the Repository movie dict with the given attributes"""
        self.all_movies[os.path.join(config.MOVIES_DIR, movie.name, config.MOVIE_DATA_DIR)] = movie   
        ChunkParser.file_to_chunks(movie, src, config.DEFAULT_READ_SIZE)


    def get_movie_by_id(self, id:str) -> Movie.Movie:
        return self.all_movies[id]
        #fallback with invalid movie id
        print(f"WARNING: MovieRepository: get_movie_by_id: No movie of id '{id}' was found.")
        return Movie.Movie(-1, "")


    def get_movie_by_name(self, name:str) -> Movie.Movie:
        for movie in self.all_movies.values():
            if movie.name == name:
                return movie

        #fallback with invalid movie name
        return Movie.Movie(str(uuid.uuid4()), "")


    def get_movie_directory(self, movie:Movie.Movie) -> str:
        for dir, m in self.all_movies.items():
            if movie == m:
                return dir
        return ""


    def copy_movie(self, movie:Movie.Movie, new_dir:str) -> None:
        ChunkCombiner.chunks_to_file(movie, self.get_movie_directory(movie), new_dir)
        
   


        