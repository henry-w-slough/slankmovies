from ..Repositories import MovieRepository
from ..Models import Movie

class MovieService:


    def __init__(self) -> None:
        """Handles all logic for creating and configuring Movies."""
        self.movie_repository = MovieRepository.MovieRepository()


    def add_movie(self, id:str, name:str, src:str) -> None:
        """Adds a movie to the Service's repository with the given characteristics."""
        new_movie = Movie.Movie(id, name)
        self.movie_repository.add_movie(new_movie, src)   

   
    def get_movie_by_id(self, id:str) -> Movie.Movie:
        return self.movie_repository.get_movie_by_id(id)


    def get_movie_by_name(self, name:str) -> Movie.Movie:
        return self.movie_repository.get_movie_by_name(name)

