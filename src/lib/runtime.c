#include <stdlib.h>
#include <stdio.h>
#include <string.h>

void error() {
    printf("runtime error\n");
    exit(1);
}

void printString(char* s) {
    printf("%s\n", s);
}

void printInt(long i) {
    printf("%ld\n", i);
}

char* readString() {
    char* str = 0;
    size_t len;
    getline(&str, &len, stdin);
    size_t end = strlen(str) - 1;
    if (str[end] == '\n')
        str[end] = '\0';
    return str;
}

long readInt() {
    long i;
    scanf("%ld", &i);
    readString();
    return i;
}


/* internal functions: */

int _compareStrings(int op, char* str1, char* str2) {
    int c = strcmp(str1, str2);
    switch(op) {
        case 0:
            return c == 0;
        case 1:
            return c != 0;
        case 2:
            return c < 0;
        case 3:
            return c <= 0;
        case 4:
            return c > 0;
        case 5:
            return c >= 0;
        default:
            return 0;
    }
}

char* _addStrings(char* str1, char* str2) {
    char* str = malloc((strlen(str1) + strlen(str2) + 1) * sizeof(char));
    strcpy(str, str1);
    strcat(str, str2);
    return str;
}
