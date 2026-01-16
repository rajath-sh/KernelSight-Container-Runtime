#define _GNU_SOURCE
#include <sched.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/wait.h>
#include <sys/mount.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <string.h>

#define STACK_SIZE (1024 * 1024)

static char child_stack[STACK_SIZE];

/* Write helper */
void write_file(const char *path, const char *value) {
    int fd = open(path, O_WRONLY | O_CLOEXEC);
    if (fd < 0) {
        perror(path);
        return;
    }
    write(fd, value, strlen(value));
    close(fd);
}

/* Setup cgroup limits */
void setup_cgroup(const char *name, pid_t pid) {
    char path[256];

    // Enable controllers
    write_file("/sys/fs/cgroup/cgroup.subtree_control", "+cpu +memory");

    // Create cgroup
    snprintf(path, sizeof(path), "/sys/fs/cgroup/%s", name);
    mkdir(path, 0755);

    // CPU limit (50%)
    snprintf(path, sizeof(path), "/sys/fs/cgroup/%s/cpu.max", name);
    write_file(path, "50000 100000");

    // Memory limit (256 MB)
    snprintf(path, sizeof(path), "/sys/fs/cgroup/%s/memory.max", name);
    write_file(path, "268435456");

    // Add process to cgroup
    snprintf(path, sizeof(path), "/sys/fs/cgroup/%s/cgroup.procs", name);
    char pid_str[32];
    sprintf(pid_str, "%d", pid);
    write_file(path, pid_str);
}

/* Container process */
int child_main(void *arg) {
    char *name = (char *)arg;

    sethostname(name, strlen(name));

    mkdir("/proc", 0555);
    mount("proc", "/proc", "proc", 0, "");

    char *const args[] = {"/bin/bash", NULL};
    execv(args[0], args);

    perror("exec");
    return 1;
}

int main(int argc, char *argv[]) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <container_name>\n", argv[0]);
        return 1;
    }

    printf("Starting container: %s\n", argv[1]);

    pid_t pid = clone(
        child_main,
        child_stack + STACK_SIZE,
        CLONE_NEWUTS | CLONE_NEWPID | CLONE_NEWNS | SIGCHLD,
        argv[1]
    );

    if (pid < 0) {
        perror("clone");
        return 1;
    }

    // Apply resource limits AFTER clone
    setup_cgroup(argv[1], pid);

    waitpid(pid, NULL, 0);
    return 0;
}
