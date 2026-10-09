#include "XdgPaths.h"

#include <QDir>
#include <QStandardPaths>

namespace CloudStream {

namespace {
QString appPath(QStandardPaths::StandardLocation location) {
    const auto suffix =
#ifdef Q_OS_WIN
        QStringLiteral("LATCHI-WATCHING-CloudStream");
#else
        QStringLiteral("latchi-watching-cloudstream");
#endif
    return QStandardPaths::writableLocation(location) + "/" + suffix;
}
}

QString XdgPaths::configDir() {
    return appPath(QStandardPaths::GenericConfigLocation);
}

QString XdgPaths::dataDir() {
    return appPath(QStandardPaths::GenericDataLocation);
}

QString XdgPaths::cacheDir() {
    return appPath(QStandardPaths::GenericCacheLocation);
}

QString XdgPaths::extensionsDir() {
    return dataDir() + "/extensions";
}

QString XdgPaths::logFile() {
    return cacheDir() + "/cloudstream.log";
}

bool XdgPaths::ensureDirectories() {
    QDir dir;
    return dir.mkpath(configDir()) && dir.mkpath(dataDir()) &&
           dir.mkpath(cacheDir()) && dir.mkpath(extensionsDir());
}

} // namespace CloudStream
