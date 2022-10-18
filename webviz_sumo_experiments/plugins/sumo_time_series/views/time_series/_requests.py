from typing import List
from fmu.sumo.explorer import Explorer
import pyarrow as pa
import time


def get_smry_vector_names(explorer: Explorer, case_uuid: str) -> List[str]:
    start_s = time.perf_counter()
    columns = explorer.sumo.get(
        "/search",
        query=f"_sumo.parent_object:{case_uuid} AND \
              class:table AND \
              data.name:summary AND \
              fmu.iteration.id:0 AND \
              fmu.realization.id:0",
        size=1,
        select="data.spec.columns",
    )["hits"]["hits"][0]["_source"]["data"]["spec"]["columns"]
    time_now = time.perf_counter()
    elapsed = time_now - start_s
    print(f"Got vector names in {elapsed:.3f}s")
    return [col for col in columns if col not in ["YEARS", "DATE"]]


def get_vector_data(explorer: Explorer, case_uuid: str, vector_name: str):
    start_s = time.perf_counter()
    res = explorer.sumo.get(
        "/search",
        query=f'_sumo.parent_object:{case_uuid} AND \
              class:table AND \
              data.name:"{vector_name}" AND \
              fmu.iteration.id:0',
        size=1,
        select=False,
    )
    hits = res["hits"]["hits"]
    obj_uuid = hits[0]["_id"]
    arwfile = explorer.sumo.get(f"/objects('{obj_uuid}')/blob")
    with pa.ipc.open_file(arwfile) as reader:
        table = reader.read_pandas()
    time_now = time.perf_counter()
    elapsed = time_now - start_s
    print(f"Got vector data for {vector_name} in {elapsed:.3f}s")
    return table
