#!/bin/bash
echo $1 $2 $3

if [ $1 = 'i' ]; then
  srun --partition=main --nodes=1 --ntasks=1 --cpus-per-task=1 --mem=4000 --time=3:00:00 --export=ALL --pty bash -i
elif [ $1 = 'r' ]; then
  [ -z "$2" ] && { echo "Subfolder?"; exit 1; }
  SUBFOLDER="$2"
  FILE_PATH="${PWD}/../${SUBFOLDER}/sim.py"

  OPTS=""
  [ -n "$3" ] && { OPTS=$3; }
  echo "OPTS=${OPTS}"

  SIM_ID=$((1 + $RANDOM % 1000))
  [ -n "$4" ] && { SIM_ID=$4; }
  JOB_NAME="sim_${SIM_ID}"
  echo "JOB_NAME=${JOB_NAME}"

  SCRIPT_NAME="sbatch_${JOB_NAME}.sh"

  echo "#!/bin/bash
#SBATCH --partition=main             # Partition (job queue)
#SBATCH --job-name=${JOB_NAME}
#SBATCH --nodes=1                    # Number of nodes you require
#SBATCH --ntasks=1                   # Total # of tasks across all nodes
#SBATCH --cpus-per-task=1            # Cores per task (>1 if multithread tasks)
#SBATCH --mem=8000                   # Real memory (RAM) required (MB)
#SBATCH --time=48:00:00              # Total run time limit (HH:MM:SS)
#SBATCH --export=ALL                 # Export your current env to the job env
#SBATCH --output=${SUBFOLDER}/log/${JOB_NAME}.out
export MV2_ENABLE_AFFINITY=0
srun --mpi=pmi2 python3 ${FILE_PATH} ${OPTS}
  " > $SCRIPT_NAME

  sbatch $SCRIPT_NAME
elif [ $1 = 'rc' ]; then
  srun_ () {
    [ -z "$1" ] && { echo "Subfolder?"; exit 1; }
    SUBFOLDER="$1"
    echo "SUBFOLDER=${SUBFOLDER}"
    [ -z "$2" ] && { echo "hetero_clusters?"; exit 1; }
    HETERO_CLUSTERS="$2"
    echo "HETERO_CLUSTERS=${HETERO_CLUSTERS}"
    [ -z "$3" ] && { echo "N_fluctuating_frac?"; exit 1; }
    N_FLUCTUATING_FRAC="$3"
    echo "N_FLUCTUATING_FRAC=${N_FLUCTUATING_FRAC}"
    [ -z "$4" ] && { echo "serv_time_rv?"; exit 1; }
    SERV_TIME_RV="$4"
    echo "SERV_TIME_RV=${SERV_TIME_RV}"

    ./srun.sh r $SUBFOLDER "--hetero_clusters=${HETERO_CLUSTERS} --N_fluctuating_frac=${N_FLUCTUATING_FRAC} --serv_time_rv=${SERV_TIME_RV}" $5
  }

  srun_w_label () {
    [ -z "$1" ] && { echo "Label? podc, ts, rr, ucb?"; exit 1; }
    SUBFOLDER="sim_$1"
    rm $SUBFOLDER/log/*

    srun_ $SUBFOLDER 0 0   'disc' # 1
    srun_ $SUBFOLDER 0 0   'exp'  # 2
    srun_ $SUBFOLDER 0 0.3 'exp'  # 3
    srun_ $SUBFOLDER 0 0.3 'exp'  # 4

    srun_ $SUBFOLDER 1 0   'disc' # 5
    srun_ $SUBFOLDER 1 0   'exp'  # 6
    srun_ $SUBFOLDER 1 0.3 'disc' # 7
    srun_ $SUBFOLDER 1 0.3 'exp'  # 8
  }

  srun_w_label 'podc'
  srun_w_label 'ts'
  srun_w_label 'rr'
  srun_w_label 'ucb'
elif [ $1 = 'l' ]; then
  squeue -u mfa51
elif [ $1 = 'k' ]; then
  scancel --user=mfa51 # -n learning
else
  echo "Arg did not match!"
fi
