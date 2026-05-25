int main() {
    int i;
    int sum;
    int j;

    i = 0;
    sum = 0;

    while (i < 5) {
        sum = sum + i;
        i = i + 1;
    }

    for (j = 0; j < 3; j = j + 1) {
        sum = sum + j;
    }

    do {
        sum = sum - 1;
    } while (sum > 10);

    printf("sum = %d\n", sum);
    return sum;
}
