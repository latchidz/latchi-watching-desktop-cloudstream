#include <QtTest>
#include <QAbstractButton>
#include <QLabel>
#include <QPixmap>
#include "../ui/LatchiSourceHub.h"

class LatchiSourceHubTest : public QObject {
    Q_OBJECT
private slots:
    void exactEightProvidersAndEmbeddedCards() {
        CloudStream::LatchiSourceHub hub;
        const auto sources = hub.sources();
        QCOMPARE(sources.size(), 8);
        QStringList ids;
        for (const auto &source : sources) {
            ids << source.id;
            QVERIFY(!source.arabic.isEmpty());
            auto *card = hub.findChild<QAbstractButton *>("latchiSource_" + source.id);
            QVERIFY(card);
            QCOMPARE(card->focusPolicy(), Qt::StrongFocus);
            QVERIFY(card->accessibleName().contains(source.arabic));
            QPixmap image(":/sourcecards/" + source.card);
            QVERIFY(!image.isNull());
            QCOMPARE(image.size(), QSize(1800, 600));
        }
        QCOMPARE(ids, QStringList({"3isk", "eseek", "Krmzy", "MyCimaProvider", "Topcinema", "TukTukcima", "Tuniflix", "Wecima"}));
        QCOMPARE(hub.layoutDirection(), Qt::RightToLeft);
    }
    void keyboardActivationAndBusyGuard() {
        CloudStream::LatchiSourceHub hub;
        hub.resize(1100, 760); hub.show();
        QSignalSpy selected(&hub, &CloudStream::LatchiSourceHub::sourceActivated);
        auto *card = hub.findChild<QAbstractButton *>("latchiSource_3isk");
        card->setFocus();
        QTest::keyClick(card, Qt::Key_Space);
        QCOMPARE(selected.size(), 1);
        QCOMPARE(selected.first().first().toString(), QString("3isk"));
        hub.setBusy(true, QString::fromUtf8("جارٍ التثبيت"));
        QVERIFY(hub.busy()); QVERIFY(!card->isEnabled());
        card->click(); QCOMPARE(selected.size(), 1);
        hub.setBusy(false); card->click(); QCOMPARE(selected.size(), 2);
    }
    void responsiveGridAndPlainTextMessages() {
        CloudStream::LatchiSourceHub hub;
        hub.resize(1100, 760); hub.show(); QTest::qWait(30);
        QCOMPARE(hub.columnCount(), 3);
        hub.resize(850, 760); QTest::qWait(30); QCOMPARE(hub.columnCount(), 2);
        hub.resize(570, 760); QTest::qWait(30); QCOMPARE(hub.columnCount(), 1);
        hub.setMessage("<script>not markup</script>", true);
        auto *message = hub.findChild<QLabel *>("latchiSourceMessage");
        QCOMPARE(message->textFormat(), Qt::PlainText);
    }
};
QTEST_MAIN(LatchiSourceHubTest)
#include "test_latchi_source_hub.moc"
