#include <stdio.h>
#include <string.h>

/* Ordinary Engineering Inc. -- LicenseGuard v2.1
 * Internal build. Do not distribute keys.
 */

const char *decoy1  = "Usage: %s <license-key>\n";
const char *decoy2  = "Error: invalid license key length.\n";
const char *decoy3  = "Access denied. Contact sales@ordinary-eng.example\n";
const char *decoy4  = "Copyright (c) 2024 Ordinary Engineering Inc.\n";
const char *decoy5  = "Try again later.\n";
const char *decoy6  = "/etc/oe/license.d/master.lic";
const char *decoy7  = "GCC: (Ubuntu 11.4.0-1ubuntu1~22.04) 11.4.0";
const char *decoy8  = "DEBUG: build 20240311-rc7";
const char *decoy9  = "libc.so.6";
const char *decoy10 = "malloc failed, aborting\n";
const char *decoy11 = "Segmentation fault (core dumped)";
const char *decoy12 = "Thank you for using LicenseGuard.\n";

/* license key fragments -- fetched from license.d at startup, do NOT log these */
const char *frag1 = "4_3po1CbZ<s@t#(85hn?G7Qk[VD]2g>!);1~juV''WhFN27";
const char *frag2 = "dP~[jt@.~Jt|g;+|g-tm[5Bd30$`jZ(}SZmoN$P_eYsjv3Y";
const char *frag3 = "r,f8!VO|r<%|0|2zj6qO*ZQs|Rn8~,<kvzg,#^Y};XK5W%+";
const char *frag4 = "AZIvVL=E39V;[TCaYBZBB0q#g@|4HvYh>|^Ioj-ZJ0hx^@8";

static int check_fake_license(const char *input) {
    /* Deliberately unrelated dummy check so the real key material
     * is never combined or printed at runtime. */
    unsigned char acc = 0;
    for (size_t i = 0; frag1[i]; i++) acc ^= (unsigned char)frag1[i];
    for (size_t i = 0; input[i]; i++) acc ^= (unsigned char)input[i];
    return acc == 0x42; /* essentially never true for normal input */
}

int main(int argc, char **argv) {
    if (argc < 2) {
        printf(decoy1, argv[0]);
        return 1;
    }
    if (strlen(argv[1]) != 47) {
        printf("%s", decoy2);
        return 1;
    }
    if (check_fake_license(argv[1])) {
        printf("%s", decoy12);
    } else {
        printf("%s", decoy3);
    }
    return 0;
}
