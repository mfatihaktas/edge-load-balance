#!/bin/bash
#SBATCH --partition=main             # Partition (job queue)
#SBATCH --job-name=sim_26
#SBATCH --nodes=1                    # Number of nodes you require
#SBATCH --ntasks=1                   # Total # of tasks across all nodes
#SBATCH --cpus-per-task=1            # Cores per task (>1 if multithread tasks)
#SBATCH --mem=8000                   # Real memory (RAM) required (MB)
#SBATCH --time=48:00:00              # Total run time limit (HH:MM:SS)
#SBATCH --export=ALL                 # Export your current env to the job env
#SBATCH --output=../sim_ucb/log/sim_26.out
export MV2_ENABLE_AFFINITY=0
srun --mpi=pmi2 python3 /home/mfa51/edge-load-balance/sim_common/../sim_ucb/sim.py --hetero_clusters=0 --N_fluctuating_frac=0 --serv_time_rv=exp
  
