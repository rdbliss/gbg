void foo();
int jump();

int main(void)
{
start:
    foo();

    if (1) {
        if (jump()) goto start;
        foo();
    }
    return 0;
}

/* solution:

int main(void)
    int goto_start = 0;

start:
    goto_start = 0;

    do {
        foo();

        if (1) {
            goto_start = jump();
            if (!goto_start) {
                foo();
            }
        }
    } while (goto_start);
}
*/

