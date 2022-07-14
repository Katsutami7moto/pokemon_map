import folium
from django.http import HttpRequest
from django.shortcuts import render
from django.utils.timezone import localtime

from .models import Pokemon, PokemonEntity

MOSCOW_CENTER = [55.751244, 37.618423]
DEFAULT_IMAGE_URL = (
    'https://vignette.wikia.nocookie.net/pokemon/images/6/6e/%21.png/revision'
    '/latest/fixed-aspect-ratio-down/width/240/height/240?cb=20130525215832'
    '&fill=transparent'
)


def add_pokemon(folium_map, lat, lon, image_url=DEFAULT_IMAGE_URL):
    icon = folium.features.CustomIcon(
        image_url,
        icon_size=(50, 50),
    )
    folium.Marker(
        [lat, lon],
        # Warning! `tooltip` attribute is disabled intentionally
        # to fix strange folium cyrillic encoding bug
        icon=icon,
    ).add_to(folium_map)


def show_all_pokemons(request: HttpRequest):
    folium_map = folium.Map(location=MOSCOW_CENTER, zoom_start=12)
    local_now = localtime()
    pokemon_entities_db = PokemonEntity.objects.filter(
        appeared_at__lte=local_now,
        disappeared_at__gte=local_now
    )
    for pokemon_entity in pokemon_entities_db:
        add_pokemon(
            folium_map, pokemon_entity.latitude,
            pokemon_entity.longitude,
            pokemon_entity.pokemon.image.path
        )

    pokemons_on_page = []
    pokemons_db = Pokemon.objects.all()
    for pokemon in pokemons_db:
        pokemons_on_page.append({
            'pokemon_id': pokemon.id,
            'img_url': request.build_absolute_uri(pokemon.image.url),
            'title_ru': pokemon.title,
        })

    return render(request, 'mainpage.html', context={
        'map': folium_map._repr_html_(),
        'pokemons': pokemons_on_page,
    })


def show_pokemon(request: HttpRequest, pokemon_id):
    requested_pokemon = Pokemon.objects.get(id=pokemon_id)
    local_now = localtime()
    shown_pokemon_entities = requested_pokemon.entities.filter(
        appeared_at__lte=local_now,
        disappeared_at__gte=local_now
    )
    folium_map = folium.Map(location=MOSCOW_CENTER, zoom_start=12)
    for pokemon_entity in shown_pokemon_entities:
        add_pokemon(
            folium_map, pokemon_entity.latitude,
            pokemon_entity.longitude,
            pokemon_entity.pokemon.image.path
        )
    shown_pokemon = {
        'title_ru': requested_pokemon.title,
        'title_en': requested_pokemon.title_en,
        'title_jp': requested_pokemon.title_jp,
        'description': requested_pokemon.description,
        'img_url': request.build_absolute_uri(requested_pokemon.image.url)
    }
    if requested_pokemon.previous_evolution:
        shown_pokemon['previous_evolution'] = {
            "title_ru": requested_pokemon.previous_evolution.title,
            "pokemon_id": requested_pokemon.previous_evolution.id,
            "img_url": request.build_absolute_uri(
                requested_pokemon.previous_evolution.image.url
            )
        }
    if requested_pokemon.next_evolutions.all():
        next_pokemon = requested_pokemon.next_evolutions.all().first()
        shown_pokemon['next_evolution'] = {
            "title_ru": next_pokemon.title,
            "pokemon_id": next_pokemon.id,
            "img_url": request.build_absolute_uri(next_pokemon.image.url)
        }
    return render(request, 'pokemon.html', context={
        'map': folium_map._repr_html_(),
        'pokemon': shown_pokemon
    })
