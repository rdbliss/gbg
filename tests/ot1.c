void foo();
int jump();

int main(void)
{
start:
    foo();

    for (int i = 0; i < 10; ++i) {
        if (jump()) goto start;
        foo();
    }
    return 0;
}

/* solution:

int main(void)
{
    int goto_start = 0;

start:
    goto_start = 0;
    1;

    do {
        for (int i = 0; i < 10; ++i) {
            goto_start = jump();
            if (goto_start) break;

            foo();
        }
    } while (goto_start);
}
*/
