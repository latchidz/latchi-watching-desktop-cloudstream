#pragma once
#include <QWidget>
#include <QList>
#include <QString>

class QAbstractButton;
class QLabel;
class QGridLayout;
class QScrollArea;

namespace CloudStream {
struct LatchiSourceDefinition {
    QString id, arabic, english, card, accent;
};

class LatchiSourceHub final : public QWidget {
    Q_OBJECT
public:
    explicit LatchiSourceHub(QWidget *parent = nullptr);
    static QList<LatchiSourceDefinition> sources();
    int columnCount() const { return columns_; }
    bool busy() const { return busy_; }
    void setBusy(bool busy, const QString &message = {});
    void setMessage(const QString &message, bool error = false);
signals:
    void sourceActivated(const QString &id);
    void extensionsRequested();
    void networkRequested();
protected:
    bool eventFilter(QObject *object, QEvent *event) override;
private:
    void relayout(int viewportWidth);
    QList<QAbstractButton *> cards_;
    QLabel *message_{};
    QGridLayout *grid_{};
    QScrollArea *scroll_{};
    int columns_ = 0;
    bool busy_ = false;
};
}
