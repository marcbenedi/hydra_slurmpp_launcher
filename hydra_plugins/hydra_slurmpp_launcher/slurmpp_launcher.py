from hydra_plugins.hydra_submitit_launcher.submitit_launcher import BaseSubmititLauncher, SlurmLauncher
from hydra_plugins.hydra_submitit_launcher.config import BaseQueueConf

from typing import Any, Dict, List, Optional, Sequence
from hydra.core.utils import JobReturn
from omegaconf import DictConfig, OmegaConf
from pathlib import Path
from hydra.core.utils import JobReturn, filter_overrides, run_job, setup_globals
from hydra_plugins.hydra_submitit_launcher.config import BaseQueueConf, SlurmQueueConf
import os
import logging
from hydra.core.singleton import Singleton
import shlex
from dataclasses import dataclass
import sys
from hydra.core.config_store import ConfigStore

log = logging.getLogger(__name__)

@dataclass
class SlurmppConf(SlurmQueueConf):
    _target_: str = (
        "hydra_plugins.hydra_slurmpp_launcher.slurmpp_launcher.SlurmppLauncher"
    )

    python_pre: Optional[str] = None
    python: Optional[str] = shlex.quote(sys.executable)

# Register as hydra launcher
ConfigStore.instance().store(
    group="hydra/launcher",
    name="slurmpp_launcher",
    node=SlurmppConf(),
    provider="slurmpp_launcher",
)


class SlurmppLauncher(SlurmLauncher):

    def __init__(self, python: str, python_pre: Optional[str], **params: Any) -> None:
        super().__init__(**params)

        self.python_pre = python_pre or ""
        self.python = python

    def launch(
        self, job_overrides: Sequence[Sequence[str]], initial_job_idx: int
    ) -> Sequence[JobReturn]:
        # lazy import to ensure plugin discovery remains fast
        import submitit

        assert self.config is not None

        num_jobs = len(job_overrides)
        assert num_jobs > 0
        params = self.params
        params["python"] = f"{self.python_pre} {self.python}"
        # build executor
        init_params = { "folder": self.params["submitit_folder"] }
        specific_init_keys = {"max_num_timeout", "python"}

        init_params.update(
            **{
                f"{self._EXECUTOR}_{x}": y
                for x, y in params.items()
                if x in specific_init_keys
            }
        )

        init_keys = specific_init_keys | {"submitit_folder"}
        executor = submitit.AutoExecutor(cluster=self._EXECUTOR, **init_params)

        # specify resources/parameters
        baseparams = set(OmegaConf.structured(BaseQueueConf).keys())
        params = {
            x if x in baseparams else f"{self._EXECUTOR}_{x}": y
            for x, y in params.items()
            if x not in init_keys
        }
        executor.update_parameters(**params)

        log.info(
            f"Submitit '{self._EXECUTOR}' sweep output dir : "
            f"{self.config.hydra.sweep.dir}"
        )
        sweep_dir = Path(str(self.config.hydra.sweep.dir))
        sweep_dir.mkdir(parents=True, exist_ok=True)
        if "mode" in self.config.hydra.sweep:
            mode = int(str(self.config.hydra.sweep.mode), 8)
            os.chmod(sweep_dir, mode=mode)

        job_params: List[Any] = []
        for idx, overrides in enumerate(job_overrides):
            idx = initial_job_idx + idx
            lst = " ".join(filter_overrides(overrides))
            log.info(f"\t#{idx} : {lst}")
            job_params.append(
                (
                    list(overrides),
                    "hydra.sweep.dir",
                    idx,
                    f"job_id_for_{idx}",
                    Singleton.get_state(),
                )
            )

        jobs = executor.map_array(self, *zip(*job_params))
        return [j.results()[0] for j in jobs]
