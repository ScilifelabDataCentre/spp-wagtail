#!/bin/sh
set -eu

BASE_HOST="ftp.ebi.ac.uk"
TARGETS_FILE="targets.txt"
DEST_ROOT="/datasets"

echo "Using targets file: $TARGETS_FILE"
echo "Destination root:   $DEST_ROOT"
echo

# fields: FLAG REMOTE_PATH LOCAL_PATH
while read -r flag remote_path local_path; do
  # Skip empty lines or comments
  [ -z "${remote_path:-}" ] && continue
  case "$remote_path" in
    \#*) continue ;;
  esac

  study_dir=$(basename "$remote_path")
  study_dir=${study_dir%/}  # strip trailing slash

  echo "=== Mirroring $study_dir ==="
  echo "  Remote: ftp://${BASE_HOST}${remote_path}"
  echo "  Local:  ${DEST_ROOT}/${study_dir}/"

  # -c: continue (resume)
  # --verbose: show what it's doing
  # remote path: $remote_path
  # local path:  $DEST_ROOT/$study_dir
  lftp -c "
    set ftp:ssl-allow no;
    open ${BASE_HOST};
    mirror -c --verbose \"${remote_path}\" \"${DEST_ROOT}/${study_dir}\";
  "

  echo
done < "$TARGETS_FILE"

echo "All mirrors attempted."
