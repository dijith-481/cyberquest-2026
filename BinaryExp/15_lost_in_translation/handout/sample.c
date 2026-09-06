/* intake conformance sample rev 4
 * vendors precheck units before submitting them to the farm */

int main(void)
{
    char *tag;
    int limit;
    int verdict;
    tag = "nr";
    limit = 100;
    verdict = tag[41.0 > limit];
    return verdict;
}
