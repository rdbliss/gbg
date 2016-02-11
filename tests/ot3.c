void foo();
int jump();

int main(void)
{
start:
    foo();

    switch (1) {
        case 0:
            if (jump()) goto start;
            foo();
            break;
        default:
            break;
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
        switch (1) {
            case 0:
                goto_start = jump();
                if (goto_start) break;
                foo();
                break;
            default:
                break;
        }
    } while (goto_start);
}
*/
