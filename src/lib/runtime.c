#include <stdlib.h>
#include <stdio.h>
#include <string.h>

void error() {
    printf("runtime error\n");
    exit(1);
}

void printString(char* s) {
    printf("%s", s);
}

void printInt(int i) {
    printf("%d\n", i);
}

void printBoolean(int b) {  // for debugging
    printf("%s\n", b ? "true" : "false");
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

int readInt() {
    int i;
    scanf("%d", &i);
    readString();
    return i;
}

int readBoolean() {  // for debugging
    return readInt();
}

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
