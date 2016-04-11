ACLOCAL_AMFLAGS = -I m4
bin_PROGRAMS=ip_activity
ip_activity_SOURCES=backend.cpp fields.c fields.h
ip_activity_LDADD=-lunirec -ltrap -lyaml-cpp
ip_activity_CXXFLAGS=-O2 -std=c++98 -Wno-write-strings
include ./aminclude.am
pkgdocdir=${docdir}/ip_activity
pkgdoc_DATA=README.md
EXTRA_DIST=README.md
