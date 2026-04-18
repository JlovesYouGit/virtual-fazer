IDENTIFICATION DIVISION.
       PROGRAM-ID. MEMORY-PARSER.
       AUTHOR. INSTAGRAN TEAM.
       DATE-WRITTEN. 2026-04-17.
       
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT USER-DATA-FILE ASSIGN TO "userdata.dat"
               ORGANIZATION IS LINE SEQUENTIAL.
           SELECT OUTPUT-FILE ASSIGN TO "parsed_data.txt"
               ORGANIZATION IS LINE SEQUENTIAL.
       
       DATA DIVISION.
       FILE SECTION.
       FD USER-DATA-FILE.
       01 USER-RECORD.
           05 USER-ID            PIC X(36).
           05 USER-NAME          PIC X(50).
           05 USER-CATEGORY      PIC X(30).
           05 BEHAVIOR-SCORE     PIC 9(3)V99.
           05 INTERACTION-COUNT  PIC 9(5).
           05 LAST-ACTIVE        PIC X(19).
           05 FILLER             PIC X(1).
       
       FD OUTPUT-FILE.
       01 OUTPUT-RECORD.
           05 PROCESSED-DATA     PIC X(200).
       
       WORKING-STORAGE SECTION.
       01 WS-USER-COUNT         PIC 9(6) VALUE 0.
       01 WS-TOTAL-SCORE        PIC 9(6)V99 VALUE 0.
       01 WS-AVG-SCORE          PIC 9(3)V99 VALUE 0.
       01 WS-CURRENT-TIME.
           05 WS-HOUR            PIC 99.
           05 WS-MINUTE          PIC 99.
           05 WS-SECOND          PIC 99.
       01 WS-EOF                 PIC X VALUE 'N'.
       01 WS-PROCESSING-FLAG    PIC X VALUE 'Y'.
       
       01 CATEGORY-COUNTERS.
           05 TECH-COUNT         PIC 9(4) VALUE 0.
           05 SOCIAL-COUNT       PIC 9(4) VALUE 0.
           05 CREATIVE-COUNT     PIC 9(4) VALUE 0.
           05 BUSINESS-COUNT    PIC 9(4) VALUE 0.
       
       01 MEMORY-BUFFER.
           05 BUFFER-SIZE        PIC 9(6) VALUE 1000000.
           05 BUFFER-POINTER     PIC 9(6) VALUE 0.
           05 BUFFER-DATA        OCCURS 1 TO 1000000 TIMES
                                   DEPENDING ON BUFFER-SIZE
                                   INDEXED BY BUF-IDX.
           10 BUFFER-USER-ID     PIC X(36).
           10 BUFFER-CATEGORY    PIC X(30).
           10 BUFFER-SCORE       PIC 9(3)V99.
       
       PROCEDURE DIVISION.
       MAIN-LOGIC.
           PERFORM INITIALIZATION
           PERFORM PROCESS-USER-DATA
               UNTIL WS-EOF = 'Y'
           PERFORM CALCULATE-STATISTICS
           PERFORM GENERATE-REPORT
           PERFORM CLEANUP
           GOBACK.
       
       INITIALIZATION.
           OPEN INPUT USER-DATA-FILE
           OPEN OUTPUT OUTPUT-FILE
           MOVE 'N' TO WS-EOF
           MOVE 0 TO WS-USER-COUNT
           MOVE 0 TO WS-TOTAL-SCORE
           PERFORM GET-CURRENT-TIME.
       
       PROCESS-USER-DATA.
           READ USER-DATA-FILE
               AT END MOVE 'Y' TO WS-EOF
               NOT AT END PERFORM PROCESS-USER-RECORD.
       
       PROCESS-USER-RECORD.
           ADD 1 TO WS-USER-COUNT
           MOVE BEHAVIOR-SCORE TO WS-AVG-SCORE
           ADD WS-AVG-SCORE TO WS-TOTAL-SCORE
           
           PERFORM UPDATE-CATEGORY-COUNTERS
           PERform STORE-IN-MEMORY-BUFFER
           PERFORM VALIDATE-USER-DATA.
       
       UPDATE-CATEGORY-COUNTERS.
           EVALUATE USER-CATEGORY
               WHEN "TECHNOLOGY"
                   ADD 1 TO TECH-COUNT
               WHEN "SOCIAL"
                   ADD 1 TO SOCIAL-COUNT
               WHEN "CREATIVE"
                   ADD 1 TO CREATIVE-COUNT
               WHEN "BUSINESS"
                   ADD 1 TO BUSINESS-COUNT
               WHEN OTHER
                   CONTINUE
           END-EVALUATE.
       
       STORE-IN-MEMORY-BUFFER.
           IF BUFFER-POINTER < BUFFER-SIZE
               ADD 1 TO BUFFER-POINTER
               SET BUF-IDX TO BUFFER-POINTER
               MOVE USER-ID TO BUFFER-USER-ID(BUF-IDX)
               MOVE USER-CATEGORY TO BUFFER-CATEGORY(BUF-IDX)
               MOVE BEHAVIOR-SCORE TO BUFFER-SCORE(BUF-IDX)
           ELSE
               PERFORM FLUSH-BUFFER
               PERFORM STORE-IN-MEMORY-BUFFER
           END-IF.
       
       FLUSH-BUFFER.
           PERFORM VARYING BUF-IDX FROM 1 BY 1
                   UNTIL BUF-IDX > BUFFER-POINTER
               PERFORM WRITE-BUFFER-RECORD
           END-PERFORM
           MOVE 0 TO BUFFER-POINTER.
       
       WRITE-BUFFER-RECORD.
           STRING
               BUFFER-USER-ID(BUF-IDX) DELIMITED BY SIZE
               "|" DELIMITED BY SIZE
               BUFFER-CATEGORY(BUF-IDX) DELIMITED BY SIZE
               "|" DELIMITED BY SIZE
               BUFFER-SCORE(BUF-IDX) DELIMITED BY SIZE
               INTO PROCESSED-DATA
           WRITE OUTPUT-RECORD.
       
       VALIDATE-USER-DATA.
           IF USER-ID = SPACES OR
              USER-NAME = SPACES OR
              BEHAVIOR-SCORE < 0 OR
              BEHAVIOR-SCORE > 100
               PERFORM LOG-INVALID-RECORD
           END-IF.
       
       LOG-INVALID-RECORD.
           DISPLAY "INVALID RECORD: " USER-ID " " USER-NAME
           MOVE USER-ID TO PROCESSED-DATA
           WRITE OUTPUT-RECORD.
       
       CALCULATE-STATISTICS.
           IF WS-USER-COUNT > 0
               COMPUTE WS-AVG-SCORE = WS-TOTAL-SCORE / WS-USER-COUNT
           END-IF.
           
           DISPLAY "TOTAL USERS PROCESSED: " WS-USER-COUNT
           DISPLAY "AVERAGE BEHAVIOR SCORE: " WS-AVG-SCORE
           DISPLAY "CATEGORY COUNTS:"
           DISPLAY "  TECHNOLOGY: " TECH-COUNT
           DISPLAY "  SOCIAL: " SOCIAL-COUNT
           DISPLAY "  CREATIVE: " CREATIVE-COUNT
           DISPLAY "  BUSINESS: " BUSINESS-COUNT.
       
       GENERATE-REPORT.
           MOVE "=== MEMORY PARSING REPORT ===" TO PROCESSED-DATA
           WRITE OUTPUT-RECORD
           
           STRING "PROCESSED USERS: " DELIMITED BY SIZE
                  WS-USER-COUNT DELIMITED BY SIZE
                  INTO PROCESSED-DATA
           WRITE OUTPUT-RECORD
           
           STRING "AVERAGE SCORE: " DELIMITED BY SIZE
                  WS-AVG-SCORE DELIMITED BY SIZE
                  INTO PROCESSED-DATA
           WRITE OUTPUT-RECORD.
       
       GET-CURRENT-TIME.
           ACCEPT WS-CURRENT-TIME FROM TIME.
       
       CLEANUP.
           CLOSE USER-DATA-FILE
           CLOSE OUTPUT-FILE
           DISPLAY "MEMORY PARSING COMPLETED SUCCESSFULLY".
