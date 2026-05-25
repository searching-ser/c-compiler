int main() {
    int option;
    int result;

    option = 2;
    result = 0;

    switch (option) {
        case 1:
            result = 10;
            break;
        case 2:
            result = 20;
            break;
        default:
            result = 30;
    }

    printf("switch result = %d\n", result);
    return result;
}
