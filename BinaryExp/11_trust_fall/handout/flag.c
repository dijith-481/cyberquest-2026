#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <unistd.h>
int main(){
srand(time(0)^getpid()*1103515245);
printf("cyberQuest{tru5t_f4ll_%08x}\n",rand());
return 0;
}
