#!/bin/bash
set -euo pipefail
compiler=$1
shift
arguments=("$@")
is_program=false
has_codegen=false
previous=''
for argument in "${arguments[@]}"; do
    if [[ "$previous" == '--crate-name' && "$argument" == 'token_metadata' ]]; then
        is_program=true
    fi
    if [[ "$argument" == --emit=*link* ]]; then
        has_codegen=true
    fi
    previous=$argument
done
if $is_program && $has_codegen; then
    observations=(
        '-Cllvm-args=-print-before=codegenprepare,finalize-isel'
        '-Cllvm-args=-print-after=codegenprepare,finalize-isel,branch-folder,block-placement,sbf-mi-pemit-peephole'
        '-Cllvm-args=-print-isel-input'
        '-Cllvm-args=-filter-print-funcs=_ZN14token_metadata9processor4uses7utilize15process_utilize17h9789c7990f4c0b83E'
        '-Cllvm-args=-debug-pass=Structure'
    )
    # Exact argv, including the appended observational flags, is retained as NUL-separated bytes.
    set -C
    printf '%s\0' "$compiler" "${arguments[@]}" "${observations[@]}" > "${TRACE_OUTPUT_DIRECTORY:-/trace}/rustc-${BASHPID}.argv"
    exec "$compiler" "${arguments[@]}" "${observations[@]}"
fi
exec "$compiler" "${arguments[@]}"
