#ifndef MINIZ_EXPORT_H
#define MINIZ_EXPORT_H

#ifdef __cplusplus
extern "C" {
#endif

/*
 * Minimal export definitions for miniz when the generated header
 * is unavailable. This is sufficient for static builds used by the
 * archive_unzipper app.
 */
#ifdef MINIZ_EXPORTS
#  if defined(_WIN32) || defined(__CYGWIN__)
#    define MINIZ_EXPORT __declspec(dllexport)
#  else
#    define MINIZ_EXPORT __attribute__((visibility("default")))
#  endif
#else
#  if defined(_WIN32) || defined(__CYGWIN__)
#    define MINIZ_EXPORT __declspec(dllimport)
#  else
#    define MINIZ_EXPORT
#  endif
#endif

#ifdef __cplusplus
} /* extern "C" */
#endif

#endif /* MINIZ_EXPORT_H */
