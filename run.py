import argparse
import os
import yaml
from datetime import datetime
import shutil
from pathlib import Path


import pygarment.data_config as data_config
from pygarment.meshgen.sim_config import PathCofig
from pygarment.meshgen.boxmeshgen import BoxMesh
from pygarment.meshgen.simulation import run_sim
from pygarment.data_config import Properties
from assets.bodies.body_params import BodyParameters
from assets.garment_programs.meta_garment import MetaGarment


def get_command_args():
    """command line arguments to control the run"""
    # https://stackoverflow.com/questions/40001892/reading-named-command-arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model_path",
        "-p",
        help="Path to the folder with target model object file (.obj) and measurement file (.yaml)",
        type=str,
    )
    parser.add_argument(
        "--model_id",
        "-m",
        help="Identifier of the model to use (without file extension)",
        type=str,
    )
    parser.add_argument(
        "--garment_path",
        "-g",
        help="Path to the garment design parameters file (.yaml)",
        type=str,
        default="assets/design_params/t-shirt.yaml",
    )
    parser.add_argument(
        "--sim_config",
        "-s",
        help="Path to simulation config",
        type=str,
        default="./assets/Sim_props/default_sim_props.yaml",
    )

    parser.add_argument(
        "--output_folder",
        "-o",
        help="Path to output folder",
        type=str,
        default="./output",
    )

    args = parser.parse_args()
    print("Commandline arguments: ", args)

    return args


def generate_garment_specification(path_to_model_measurement_file, garment_path):
    model_measurements = BodyParameters(path_to_model_measurement_file)
    with open(garment_path, "r") as f:
        garment_design = yaml.safe_load(f)["design"]

    garment = MetaGarment(
        os.path.splitext(os.path.basename(garment_path))[0],
        model_measurements,
        garment_design,
    )

    pattern = garment.assembly()

    if garment.is_self_intersecting():
        print(f"{garment.name} is Self-intersecting")

    # Save as json file
    sys_props = Properties("./system.json")
    folder = pattern.serialize(
        Path(os.path.join(sys_props["output"], "intermediates")),
        tag="_" + datetime.now().strftime("%y%m%d-%H-%M-%S"),
        to_subfolder=True,
        with_3d=False,
        with_text=False,
        view_ids=False,
        with_printable=False,
    )

    return os.path.join(folder, os.path.basename(folder) + "_specification.json")


def run_simulation(
    path_to_model_mesh, path_to_garment_specification, path_to_sim_config
):
    props = data_config.Properties(path_to_sim_config)
    props.set_section_stats(
        "sim",
        fails={},
        sim_time={},
        spf={},
        fin_frame={},
        body_collisions={},
        self_collisions={},
    )
    props.set_section_stats("render", render_time={})

    spec_path = Path(path_to_garment_specification)
    garment_name, _, _ = spec_path.stem.rpartition(
        "_"
    )  # assuming ending in '_specification'

    model_id = os.path.splitext(os.path.basename(path_to_model_mesh))[0]
    sys_props = data_config.Properties("./system.json")
    paths = PathCofig(
        in_element_path=spec_path.parent,
        out_path=os.path.join(sys_props["output"], "intermediates"),
        in_name=garment_name,
        body_name=model_id,
        smpl_body=True,
        add_timestamp=True,
    )

    garment_box_mesh = BoxMesh(
        paths.in_g_spec, props["sim"]["config"]["resolution_scale"]
    )
    garment_box_mesh.load()
    garment_box_mesh.serialize(
        paths, store_panels=False, uv_config=props["render"]["config"]["uv_texture"]
    )

    # props.serialize(paths.element_sim_props)

    run_sim(
        garment_box_mesh.name,
        props,
        paths,
        save_v_norms=False,
        store_usd=False,  # NOTE: False for fast simulation!
        optimize_storage=False,  # props['sim']['config']['optimize_storage'],
        verbose=False,
    )


if __name__ == "__main__":
    args = get_command_args()
    print(f"Model path: {args.model_path}")
    print(f"Model ID: {args.model_id}")
    print(f"Garment path: {args.garment_path}")
    print(f"Simulation config path: {args.sim_config}")

    path_to_model_measurement_file = os.path.join(
        args.model_path, args.model_id + ".yaml"
    )
    path_to_model_mesh = os.path.join(args.model_path, args.model_id + ".obj")

    path_to_garment_specification = generate_garment_specification(
        path_to_model_measurement_file, args.garment_path
    )

    run_simulation(path_to_model_mesh, path_to_garment_specification, args.sim_config)
