void foo();
int jump();

int main(void)
{
    if (jump()) goto mid;

    foo();

    if (1) {
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

    if (goto_mid || 1) {
        if (!goto_mid) {
        }
    mid:
        foo();
    }
    return 0;

    foo();
}
*/
