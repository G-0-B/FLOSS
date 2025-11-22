#!/bin/bash
# ARF/scripts/merge_phase.sh

PHASE=$1  # phase1, phase2, phase3

if [ -z "$PHASE" ]; then
  echo "Usage: $0 <phase>"
  echo "Example: $0 phase1"
  exit 1
fi

case $PHASE in
  phase1)
    BRANCHES=$(git branch -r | grep "parallel/phase1-task")
    TARGET="dev/phase1-complete"
    ;;
  phase2)
    BRANCHES=$(git branch -r | grep "parallel/phase2-task")
    TARGET="dev/phase2-complete"
    ;;
  phase3)
    BRANCHES=$(git branch -r | grep "parallel/phase3-task")
    TARGET="dev/phase3-complete"
    ;;
  *)
    echo "Invalid phase: $PHASE"
    echo "Must be one of: phase1, phase2, phase3"
    exit 1
    ;;
esac

if [ -z "$BRANCHES" ]; then
  echo "No branches found for $PHASE"
  exit 1
fi

# Create target branch
git checkout -b $TARGET

# Merge each task branch
for BRANCH in $BRANCHES; do
  echo "Merging $BRANCH..."
  git merge --no-ff $BRANCH -m "Merge $(basename $BRANCH)"

  # Run tests after each merge
  # Assuming run_tests.sh is in the same directory or adjust path as needed
  # The guide said ARF/dev/scripts/run_tests.sh, but we are in ARF/scripts
  # We will try to find it or just warn if missing for now as this is a template
  if [ -f "./ARF/dev/scripts/run_tests.sh" ]; then
      ./ARF/dev/scripts/run_tests.sh
      if [ $? -ne 0 ]; then
        echo "ERROR: Tests failed after merging $BRANCH"
        exit 1
      fi
  elif [ -f "./scripts/run_tests.sh" ]; then
      ./scripts/run_tests.sh
      if [ $? -ne 0 ]; then
        echo "ERROR: Tests failed after merging $BRANCH"
        exit 1
      fi
  else
      echo "WARNING: run_tests.sh not found, skipping automated tests."
  fi
done

echo "Phase $PHASE merge complete!"
# git push origin $TARGET # Commented out for safety, user should push manually
echo "Verify the merge and run: git push origin $TARGET"
