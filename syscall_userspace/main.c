#include <stdio.h>
#include <sys/syscall.h>
#include <time.h>
#include <unistd.h>

#define CSV_FILE "utilization.csv"

int main(int argc, char *argv[]) {
  if (argc != 2) {
    perror("Usage: ./main path/to/file");
    return 1;
  }

  FILE *fp = fopen(argv[1], "w");

  if (!fp) {
    perror("Failed to open CSV file");
    return 1;
  }

  fprintf(fp, "time,utilization\n");
  fflush(fp);

  for (;;) {
    long result = syscall(491);

    if (result < 0) {
      perror("System call error");
      fclose(fp);
      return 1;
    }

    double utilization = result / 100.0;

    time_t now = time(NULL);
    struct tm *tm_info = localtime(&now);

    char time_buffer[32];
    strftime(time_buffer, sizeof(time_buffer), "%Y-%m-%d %H:%M:%S", tm_info);

    fprintf(fp, "%s,%.2f\n", time_buffer, utilization);
    fflush(fp);

    sleep(1);
  }

  fclose(fp);
  return 0;
}
