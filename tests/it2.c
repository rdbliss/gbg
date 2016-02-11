void foo();
int jump();

int main(void)
{
    int var;
    if (jump()) goto mid;

    foo();

    switch (var) {
        case 1:
            foo();
        mid:
            break;

        default:
            break;
    }

    return 0;
}

/* solution:

int main(void)
{
    int goto_mid = 0;
    int switch_var_1 = 0;
    int var;

    goto_mid = jump();
    if (!goto_mid) {
        foo();
        switch_var_0 = var;
    } else switch_var_0 = 1;

    switch (switch_var_1) {
        case 1:
            if (!goto_mid) {
                foo();
            }
        mid:
            break;

        default:
            break;
    }

    foo();
    return 0;
}
*/

