QT += widgets testlib
CONFIG += testcase c++17
TEMPLATE = app
TARGET = test_latchi_source_hub
SOURCES += test_latchi_source_hub.cpp ../ui/LatchiSourceHub.cpp
HEADERS += ../ui/LatchiSourceHub.h
RESOURCES += ../resources.qrc

win32: QMAKE_CXXFLAGS += /utf-8
