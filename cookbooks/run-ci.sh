#!/usr/bin/env bash
# Cookbook CI runner — PAT-0044 enforcement.
#
# Walks every cookbooks/<slug>/ (skipping _template/, _demos/, _archive/),
# validates meta.toml, ensures a venv, installs deps, runs each numbered
# step in order. Fails closed on any error.
#
# In production CI this is wired via .github/workflows/cookbook-test.yml
# (authored separately). This shell harness is the single-machine equivalent.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
WHEEL="${ARCFLOW_WHEEL:-/Users/gudjon/code/arcflow/python/dist/oz_arcflow-0.7.2-py3-none-any.whl}"

if [ ! -f "${WHEEL}" ]; then
    echo "FATAL: arcflow wheel not found at ${WHEEL}" >&2
    echo "Build it: cd /Users/gudjon/code/arcflow/python && bash build_wheel.sh" >&2
    exit 1
fi

# PAT-0044 — ensure docs/cookbooks-index.mdx is in sync with cookbooks/*/meta.toml.
INDEX_GEN="${ROOT}/../scripts/generate-cookbook-index.py"
INDEX_OUT="${ROOT}/../docs/cookbooks-index.mdx"
if [ -f "${INDEX_GEN}" ]; then
    if [ -f "${INDEX_OUT}" ]; then
        BEFORE_HASH="$(shasum -a 256 "${INDEX_OUT}" | awk '{print $1}')"
    else
        BEFORE_HASH=""
    fi
    python3 "${INDEX_GEN}" >/dev/null
    AFTER_HASH="$(shasum -a 256 "${INDEX_OUT}" | awk '{print $1}')"
    if [ "${BEFORE_HASH}" != "${AFTER_HASH}" ]; then
        echo "FATAL: docs/cookbooks-index.mdx is stale." >&2
        echo "       Regenerate with: python3 scripts/generate-cookbook-index.py" >&2
        echo "       Then commit the updated file." >&2
        exit 1
    fi
fi

failures=()
ok=()

for recipe_dir in "${ROOT}"/*/; do
    slug="$(basename "${recipe_dir}")"
    case "${slug}" in
        _template|_demos|_archive)
            continue
            ;;
    esac

    if [ ! -f "${recipe_dir}/meta.toml" ]; then
        echo "[${slug}] no meta.toml — skipping (not a recipe)"
        continue
    fi

    echo
    echo "=========================================="
    echo "Running: ${slug}"
    echo "=========================================="

    cd "${recipe_dir}"

    # Ensure venv with deps + wheel installed.
    if [ ! -d ".venv" ]; then
        python3 -m venv .venv
        .venv/bin/pip install --quiet --upgrade pip
    fi
    .venv/bin/pip install --quiet pyarrow duckdb numpy "${WHEEL}" 2>&1 | tail -3

    failed=0
    for step in $(ls [0-9]*.py 2>/dev/null | sort); do
        echo
        echo "  >>> ${step}"
        if ! .venv/bin/python "${step}"; then
            failures+=("${slug}/${step}")
            failed=1
            break
        fi
    done

    cd "${ROOT}"

    if [ "${failed}" -eq 0 ]; then
        ok+=("${slug}")
    fi
done

echo
echo "=========================================="
echo "Cookbook CI summary"
echo "=========================================="
for s in "${ok[@]+"${ok[@]}"}"; do
    echo "  ✓ ${s}"
done
for f in "${failures[@]+"${failures[@]}"}"; do
    echo "  ✗ ${f}"
done

if [ "${#failures[@]:-0}" -gt 0 ]; then
    exit 1
fi

echo
echo "All recipes green."
