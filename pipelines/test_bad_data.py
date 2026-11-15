"""Pipeline de test du gate de données (Lab 3) : sur des données corrompues, il doit ÉCHOUER.

    ingest -> corrupt_data -> validate_data (échec attendu) -> prepare_features (jamais lancé)

Les bugs injectés sont ceux de params.yaml (simulation.corrupt) : salaire mensuel exporté en
annuel, code de département inconnu, statut de départ manquant. Le run réussit son test
quand il est FAILED avec validate-data en échec et prepare-features jamais exécuté.
Compilation : python -m pipelines.test_bad_data   (écrit test_bad_data.yaml)
"""

from kfp import compiler, dsl
from kfp.dsl import Dataset, Input, Output

from pipelines.components import (
    PIPELINE_IMAGE,
    ingest_data,
    prepare_features,
    validate_data,
)


@dsl.component(base_image=PIPELINE_IMAGE, install_kfp_package=False)
def corrupt_data(raw_data: Input[Dataset], corrupted: Output[Dataset]) -> None:
    """Injecte les bugs « silencieux » de params.yaml (python -m src.simulate corrupt)."""
    from pipelines.stage import run_stage

    clean, bad = "data/raw/clean.csv", "data/raw/corrupted.csv"
    run_stage(
        "src.simulate",
        args=["corrupt", clean, bad],
        inputs={clean: raw_data.path},
        outputs={bad: corrupted.path},
    )


@dsl.pipeline(name="scoring-bad-data-test", description="Le gate doit refuser ces données")
def bad_data_pipeline():
    ingest_task = ingest_data()
    ingest_task.set_memory_limit("512Mi")
    corrupt_task = corrupt_data(raw_data=ingest_task.outputs["raw_data"])
    corrupt_task.set_memory_limit("512Mi")
    validate_task = validate_data(raw_data=corrupt_task.outputs["corrupted"])
    validate_task.set_memory_limit("1Gi")
    validate_task.set_caching_options(enable_caching=False)  # le gate doit vraiment tourner
    prep_task = prepare_features(raw_data=corrupt_task.outputs["corrupted"])
    prep_task.after(validate_task)  # ne doit jamais s'exécuter
    prep_task.set_memory_limit("1Gi")


if __name__ == "__main__":
    compiler.Compiler().compile(bad_data_pipeline, package_path="test_bad_data.yaml")
