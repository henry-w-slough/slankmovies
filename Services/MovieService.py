from ..Repositories import MovieRepository
from ..Models import Movie
from ..Exceptions import movie_exceptions

class MovieService:


    def __init__(self) -> None:
        """Handles all logic for creating and configuring Movies."""
        self.movie_repository = MovieRepository.MovieRepository()


    def add_movie(self, id:str, name:str, src:str) -> None:
        """Adds a movie to the Service's repository with the given characteristics."""
        new_movie = Movie.Movie(id, name)
        self.movie_repository.add_movie(new_movie, src)   

   
    def get_movie_by_id(self, id:str) -> Movie.Movie:
        movie = self.movie_repository.get_movie_by_id(id)

        if not movie:
            raise movie_exceptions.MovieNotFoundException(f"ERROR: Movie not found by Id: {id}")
        return movie


    def get_movie_by_name(self, name:str) -> Movie.Movie:
        movie = self.movie_repository.get_movie_by_name(name)

        if not movie:
            raise movie_exceptions.MovieNotFoundException(f"ERROR: Movie not found by name: {name}")
        return movie


    def copy_movie(self, movie:Movie.Movie, new_dir:str) -> None:
        self.movie_repository.copy_movie(movie, new_dir)
        

