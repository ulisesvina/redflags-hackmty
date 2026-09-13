import json
import os
import random
from datetime import date
from pathlib import Path

from data_estate.generate import Generator, write_estate
from data_estate.validate import check

ALL_SCHEMES = ["efos", "kickback", "roundtrip", "duplicate"]


def test_five_daily_seeds_validate(tmp_path: Path):
    rng = random.Random(os.environ.get("BATCH_SEED", date.today().isoformat()))
    seeds = rng.sample(range(1_000, 100_000), 5)
    random_subset = rng.sample(ALL_SCHEMES, rng.randint(1, len(ALL_SCHEMES)))
    scheme_sets = [ALL_SCHEMES, [], random_subset]

    for index, seed in enumerate(seeds):
        schemes = scheme_sets[index % len(scheme_sets)]
        estate = Generator(seed).build(schemes)
        out = tmp_path / f"c{seed}"
        write_estate(estate, out)

        errs = check(out)
        assert errs == [], f"seed {seed} schemes {schemes}: {errs[:5]}"

        truth = json.loads(
            (out / "hidden" / "ground_truth.json").read_text(encoding="utf-8")
        )
        assert len(truth["schemes"]) == len(schemes)
        assert len(truth["decoys"]) == 5
