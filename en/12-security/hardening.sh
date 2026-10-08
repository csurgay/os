#!/bin/bash
# hardening.sh - a small checksec: which protections does an ELF program use?
# usage: bash hardening.sh PROGRAM...
# Everything comes from readelf: the ELF type, the program headers, the
# dynamic section, the symbol table and the GNU property note.
for f in "$@"; do
    hdr=$(readelf -hW "$f"); ph=$(readelf -lW "$f"); dyn=$(readelf -dW "$f")
    syms=$(readelf --dyn-syms -W "$f"); notes=$(readelf -nW "$f")
    # PIE: an executable linked as a position-independent "shared object"
    if grep -q 'Type:.*DYN' <<<"$hdr" && grep -q 'PIE' <<<"$dyn"; then pie=yes
    elif grep -q 'Type:.*DYN' <<<"$hdr"; then pie="DSO"; else pie=no; fi
    # NX: the GNU_STACK header asks for a stack without the E (execute) flag
    if grep -E 'GNU_STACK' <<<"$ph" | grep -q 'RWE'; then nx=no; else nx=yes; fi
    # RELRO: GNU_RELRO segment; "full" if all symbols are bound at start (BIND_NOW)
    if grep -q GNU_RELRO <<<"$ph"; then
        if grep -q -E 'BIND_NOW|FLAGS_1.*NOW' <<<"$dyn"; then relro=full; else relro=partial; fi
    else relro=no; fi
    # canary and FORTIFY_SOURCE: imported checking functions
    grep -q '__stack_chk_fail' <<<"$syms" && canary=yes || canary=no
    nfort=$(grep -o -E '__[a-z]+_chk' <<<"$syms" | grep -v stack_chk | sort -u | wc -l)
    # CET: the GNU property note marks support for IBT and the shadow stack
    cet=$(grep -o -E 'x86 feature: .*' <<<"$notes" | sed -e 's/x86 feature: //' -e 's/, x86 ISA.*//')
    printf '%-22s PIE=%-3s NX=%-3s RELRO=%-7s canary=%-3s fortified=%-2s CET=%s\n' \
        "$(basename "$f")" "$pie" "$nx" "$relro" "$canary" "$nfort" "${cet:-none}"
done
