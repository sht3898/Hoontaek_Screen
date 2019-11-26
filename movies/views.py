from django.shortcuts import render,redirect,get_object_or_404
from .models import Movie, Genre, Review
from .forms import ReviewForm
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden,HttpResponse,JsonResponse
import requests
from django.core import serializers
import pprint
from django.db.models import Avg, Max, Min, Sum
from django.contrib.auth import get_user_model
import json

# Create your views here.
def index(request, page_type):
    movies = Movie.objects.all()
    index_movies = Movie.objects.filter(movie_type="now_playing").order_by('-popularity')[:10]    
    # user_rated_movies = Movie.objects.order_by("-avgscore")[:10]
    print(index_movies)
    if page_type == 1:
        top_rated_movies = Movie.objects.filter(movie_type="top_rated").order_by('-popularity')[:10]
        context = {
            'movies': top_rated_movies,
        }
    elif page_type == 2:
        popul_movies = Movie.objects.filter(movie_type="now_playing").order_by('-popularity')[:10]
        context = {
            'movies': popul_movies,
        }
    elif page_type == 3:
        if request.user.is_authenticated:
            for movie in request.user.like_movies.all():
                url = f'https://api.themoviedb.org/3/movie/{movie.id}/recommendations?api_key=1dfd52c8a24a0f38f40efe41c86be13b&language=ko-KR&page=1'
                response = requests.get(url).json()
                pprint.pprint(response["results"])
                movies = response["results"]
                pprint.pprint(movies)
            context = {
                'movies': movies
            }
        else:
            context = {
                'movies': index_movies
            }
    else:
        context = {
            'movies': index_movies
        }
    return render(request,'movies/index.html',context)

def detail(request,movie_pk):
    movie = get_object_or_404(Movie,pk=movie_pk)
    reviewform = ReviewForm()
    avg_score = 0
    reviews = Review.objects.filter(movie_id=movie_pk)
    # print(reviews.avgscore)
    # print(reviews.filter(movie_id=movie_pk).aggregate(Avg('score')))
    for review in reviews:
        avg_score += review.score
    if reviews.count() > 0:
        avg_score /= reviews.count()
        avg_score = round(avg_score, 2)
    else:
        avg_score = 0
    context = {
        'movie' : movie,   
        'form' : reviewform,
        'avg_score': avg_score,
    }
    return render(request,'movies/detail.html', context)

@login_required
def review(request, movie_pk):
    reviews = Review.objects.filter(movie_id=movie_pk)
    movie = get_object_or_404(Movie,pk=movie_pk)
    reviewForm = ReviewForm(request.POST)
    if reviewForm.is_valid():
        review = reviewForm.save(commit=False)
        review.movie_id = movie_pk
        review.user = request.user
        # movie.avgscore = reviews.aggregate(Avg('score'))
        # print(movie.avgscore)
        review.save()
        return redirect('movies:detail', movie_pk)
    context = {
        'movie' : movie,   
        'form' : reviewForm
    }
    return render(request,'movies/detail.html', context)

def reviewDelete(request, movie_pk,review_pk):
    reviews = Review.objects.filter(movie_id=movie_pk)
    review = get_object_or_404(Review,pk=review_pk)
    movie = get_object_or_404(Movie, pk=movie_pk)
    if request.user == review.user:
        review.delete()
        # movie.avgscore = reviews.aggregate(Avg('score'))
        # print(movie.avgscore)
    return redirect('movies:detail', movie_pk)

@login_required
def like(request, movie_pk):
    if request.is_ajax():
        movie = get_object_or_404(Movie, pk=movie_pk)
        is_liked = True
        if request.user in movie.like_users.all():
            movie.like_users.remove(request.user)
            movie.sum_likes = movie.aggregate(Sum('like_users'))
            is_liked = False
        else:
            movie.like_users.add(request.user)
            is_liked = True
        context = {
            'is_liked' : is_liked,
            'like_count' : movie.like_users.count()
        }
        return JsonResponse(context)
    else:
        return HttpResponseForbidden


def recommand(request):
    movie = Review.objects.all()
    context = {
        'max_movie' : movie
    }
    return render(request,'movies/recommand.html',context)
    
def search(request):
    query = request.GET.get('search_title')
    if query:
        title_movies = Movie.objects.filter(title__icontains=query)
        description_movies = Movie.objects.filter(description__icontains=query)
        des_movies = description_movies.difference(title_movies)
        context = {
            "title_movies" : title_movies,
            "des_movies" : des_movies
        }
        return render(request,'movies/search.html',context)
    else:
        return redirect('movies:index', 0)