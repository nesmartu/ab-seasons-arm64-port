// Verify ARM32 bionic layouts translated by the experimental HLE.
#include <stddef.h>
#include <netdb.h>
#include <dirent.h>
_Static_assert(sizeof(struct addrinfo)==32, "ARM32 addrinfo size");
_Static_assert(offsetof(struct addrinfo,ai_canonname)==20, "canonname offset");
_Static_assert(offsetof(struct addrinfo,ai_addr)==24, "sockaddr offset");
_Static_assert(offsetof(struct addrinfo,ai_next)==28, "next offset");
_Static_assert(sizeof(struct dirent)==280, "dirent size");
_Static_assert(offsetof(struct dirent,d_name)==19, "directory name offset");
