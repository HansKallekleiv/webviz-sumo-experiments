from io import BytesIO

from fmu.sumo.explorer import Explorer
import pandas as pd
import time


def get_case_uuids_with_volumetrics(explorer: Explorer, field_id):
    hits = explorer.sumo.get(
        "/search",
        query=f"class:table AND  \
                data.content:volumes AND \
                masterdata.smda.field.identifier:{field_id} AND \
                fmu.realization.id:0 AND \
                fmu.iteration.id:0",
        select="_sumo.parent_object",
    )["hits"]["hits"]
    if not hits:
        return []
    return list(set([hit["_source"]["_sumo"]["parent_object"] for hit in hits]))


def get_volumetrics_names_for_case_uuid(explorer: Explorer, case_uuid, iteration_id=0):
    hits = explorer.sumo.get(
        "/search",
        query=f"_sumo.parent_object:{case_uuid} AND \
                  class:table AND \
                  data.content:volumes AND \
                  fmu.realization.id:0 AND \
                  fmu.iteration.id:{iteration_id}",
        select="data.name",
    )["hits"]["hits"]
    if not hits:
        return []
    return [hit["_source"]["data"]["name"] for hit in hits]


def get_realizations_for_volumetric_name(
    explorer: Explorer, case_uuid, iteration_id, volumetric_name
):

    hits = explorer.sumo.get(
        "/search",
        query=f"_sumo.parent_object:{case_uuid} AND \
                class:table AND  \
                data.content:volumes AND \
                data.name:{volumetric_name} AND \
                fmu.iteration.id:{iteration_id}",
        select="fmu.realization.id",
    )["hits"]["hits"]
    if not hits:
        return []
    return [hit["_source"]["fmu"]["realization"]["id"] for hit in hits]


def get_realization_volumetrics(
    explorer: Explorer,
    case_uuid: str,
    iteration_id: str,
    volumetric_name: str,
    realization_id: str = 0,
):

    hits = explorer.sumo.get(
        "/search",
        query=f"_sumo.parent_object:{case_uuid} AND \
              class:table AND \
              data.content:volumes AND \
              data.name:{volumetric_name} AND \
              fmu.iteration.id:{iteration_id} AND \
              fmu.realization.id:{realization_id}",
        size=1,
        select=False,
    )["hits"]["hits"]
    if not hits:
        return None
    obj_uuid = hits[0]["_id"]
    return pd.read_csv(BytesIO(explorer.sumo.get(f"/objects('{obj_uuid}')/blob")))


def get_ensemble_volumetrics(
    explorer: Explorer, case_uuid: str, iteration_id: str, volumetric_name: str
):
    reals = get_realizations_for_volumetric_name(
        explorer, case_uuid, iteration_id, volumetric_name
    )
    dfs = []
    for real in reals:
        hits = explorer.sumo.get(
            "/search",
            query=f"_sumo.parent_object:{case_uuid} AND \
              class:table AND \
              data.content:volumes AND \
              data.name:{volumetric_name} AND \
              fmu.iteration.id:{iteration_id} AND \
              fmu.realization.id:{real}",
            size=1,
            select=False,
        )["hits"]["hits"]
        if not hits:
            continue
        obj_uuid = hits[0]["_id"]
        df = pd.read_csv(BytesIO(explorer.sumo.get(f"/objects('{obj_uuid}')/blob")))
        df["REAL"] = real
        dfs.append(df)
    if not dfs:
        return None
    return pd.concat(dfs)
