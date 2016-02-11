void foo();
int jump();

int main(void)
{
    if (jump()) goto mid;

    foo();

    for (int i = 0; i < 10; ++i) {
    mid:
        foo();
    }
    return 0;

    foo();
}

/* solution:

int main(void)
{
    int goto_mid = 0;

    goto_mid = jump();
    if (!goto_mid) {
        foo();
    }

    for (int i = 0; goto_mid || (i < 10); ++i) {
        if (!goto_mid) {
        }
        mid:
            goto_mid = 0;
            foo();
    }

    foo();
    return 0;
}
*/
