void cleanup();
void foo();
int jump();

int main(void)
{
    if (jump()) goto end;

    while (1) {
        for (int i = 0; i < 100; ++i) {
            foo();
        }
    }

end:
    cleanup();
    return 0;
}

/* solution:

int main(void)
{
    int goto_end = 0;

    if (!jump()) {
        while (1) {
            for (int i = 0; i < 100; ++i) {
                foo();
            }
        }
    }

end:
    goto_end = 0;
    cleanup();
    return 0;
}
*/
