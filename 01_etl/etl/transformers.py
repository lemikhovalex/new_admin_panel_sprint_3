from typing import List

import pandas as pd

from .data_structures import ESPerson, MergedFromPg, ToES
from .etl_interfaces import ITransformer
from .state import JsonFileStorage, State


def filter_persons(df: pd.DataFrame, role: str) -> List[ESPerson]:
    persons = df[["person_id", "person_full_name", "role"]]
    list_of_p = (
        persons.query(
            "role == '{role}'".format(role="writer"),
        )
        .drop(columns=["role"])
        .drop_duplicates()
        .to_dict("records")
    )
    return [
        ESPerson(id=p["person_id"], name=p["person_full_name"])
        for p in list_of_p
    ]


class PgToESTransformer(ITransformer):
    def transform(self, merged_data: List[MergedFromPg]) -> List[ToES]:
        df = pd.DataFrame(merged_data)
        movies_ids = df["film_work_id"].unique()
        out: List[ToES] = []
        for movie_id in movies_ids:
            movie_df = df.query(
                "film_work_id == '{fwid}'".format(fwid=movie_id)
            )
            writers = filter_persons(df, "writer")
            actors = filter_persons(df, "actor")
            directors = filter_persons(df, "director")
            movie_data = {
                "film_work_id": movie_id,
                "imdb_rating": movie_df["imdb_rating"].values[0],
                "genre_name": movie_df["genre_name"].unique().tolist(),
                "title": movie_df["title"].values[0],
                "description": movie_df["description"].values[0],
                "actors": actors,
                "writers": writers,
                "directors": [dir.name for dir in directors],
                "actors_names": [act.name for act in actors],
                "writers_names": [writ.name for writ in writers],
            }
            out.append(ToES.parse_obj(movie_data))
        return out