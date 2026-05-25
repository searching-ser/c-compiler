float power(float x, int n) {
    if (n == 0) {
        return 1.0;
    }
    return x * power(x, n - 1);
}

float factorialf(int n) {
    if (n <= 1) {
        return 1.0;
    }
    return n * factorialf(n - 1);
}

float exp_taylor(float x, int n) {
    if (n == 0) {
        return 1.0;
    }
    return exp_taylor(x, n - 1) + power(x, n) / factorialf(n);
}

int main() {
    float result;
    result = exp_taylor(1.0, 6);
    printf("exp_taylor(1, 6) = %f\n", result);
    return 0;
}
