void cleanup();
void foo();
int jump();

int main(void)
{
loop:
    foo();

    if (jump()) goto loop;

    cleanup();
    return 0;
}

/* solution:

int main(void)
{
    int goto_end = 0;

loop:
    goto_loop = 0;
    do {
        foo();
    } while (jump());

    return 0;
}
*/
