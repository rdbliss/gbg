int jump();
int foo();

int main(void)
{
    switch (1) {
        case 0:
            if (jump()) goto end;

            foo();
        end:
            break;
        default:
            break;
    }
    return 0;
}

/* solution:

int main(void)
{
    int goto_end = 0;

    switch (1) {
        case 0:
            if (!jump()) {
                foo();
            }

        end:
            goto_end = 0;
            break;
        default:
            break;
    }
    return 0;
}
*/
