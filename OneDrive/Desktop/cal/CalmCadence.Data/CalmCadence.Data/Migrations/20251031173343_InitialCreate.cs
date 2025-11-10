using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace CalmCadence.Data.CalmCadence.Data.Migrations
{
    /// <inheritdoc />
    public partial class InitialCreate : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.CreateTable(
                name: "Events",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "TEXT", nullable: false),
                    Title = table.Column<string>(type: "TEXT", maxLength: 500, nullable: false),
                    Description = table.Column<string>(type: "TEXT", maxLength: 4000, nullable: true),
                    Start = table.Column<DateTimeOffset>(type: "TEXT", nullable: false),
                    End = table.Column<DateTimeOffset>(type: "TEXT", nullable: false),
                    IsAllDay = table.Column<bool>(type: "INTEGER", nullable: false),
                    Location = table.Column<string>(type: "TEXT", maxLength: 1000, nullable: true),
                    ExternalId = table.Column<string>(type: "TEXT", nullable: true),
                    Source = table.Column<int>(type: "INTEGER", nullable: false),
                    CalendarId = table.Column<string>(type: "TEXT", nullable: true),
                    RecurrenceRule = table.Column<string>(type: "TEXT", maxLength: 2000, nullable: true),
                    CreatedAt = table.Column<DateTimeOffset>(type: "TEXT", nullable: false),
                    UpdatedAt = table.Column<DateTimeOffset>(type: "TEXT", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Events", x => x.Id);
                });

            migrationBuilder.CreateTable(
                name: "Habits",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "TEXT", nullable: false),
                    Name = table.Column<string>(type: "TEXT", maxLength: 200, nullable: false),
                    Description = table.Column<string>(type: "TEXT", maxLength: 2000, nullable: true),
                    Type = table.Column<int>(type: "INTEGER", nullable: false),
                    TargetValue = table.Column<double>(type: "REAL", nullable: true),
                    Unit = table.Column<string>(type: "TEXT", nullable: true),
                    ScheduleJson = table.Column<string>(type: "TEXT", maxLength: 4000, nullable: true),
                    ColorHex = table.Column<string>(type: "TEXT", maxLength: 9, nullable: true),
                    IsArchived = table.Column<bool>(type: "INTEGER", nullable: false),
                    CreatedAt = table.Column<DateTimeOffset>(type: "TEXT", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Habits", x => x.Id);
                });

            migrationBuilder.CreateTable(
                name: "Projects",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "TEXT", nullable: false),
                    Name = table.Column<string>(type: "TEXT", maxLength: 200, nullable: false),
                    Description = table.Column<string>(type: "TEXT", maxLength: 2000, nullable: true),
                    ColorHex = table.Column<string>(type: "TEXT", maxLength: 9, nullable: true),
                    CreatedAt = table.Column<DateTimeOffset>(type: "TEXT", nullable: false),
                    ArchivedAt = table.Column<DateTimeOffset>(type: "TEXT", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Projects", x => x.Id);
                });

            migrationBuilder.CreateTable(
                name: "Routines",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "TEXT", nullable: false),
                    Name = table.Column<string>(type: "TEXT", maxLength: 200, nullable: false),
                    Description = table.Column<string>(type: "TEXT", maxLength: 2000, nullable: true),
                    StepsJson = table.Column<string>(type: "TEXT", maxLength: 8000, nullable: false),
                    ScheduleJson = table.Column<string>(type: "TEXT", maxLength: 4000, nullable: false),
                    Enabled = table.Column<bool>(type: "INTEGER", nullable: false),
                    ColorHex = table.Column<string>(type: "TEXT", maxLength: 9, nullable: true),
                    CreatedAt = table.Column<DateTimeOffset>(type: "TEXT", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Routines", x => x.Id);
                });

            migrationBuilder.CreateTable(
                name: "Settings",
                columns: table => new
                {
                    Id = table.Column<int>(type: "INTEGER", nullable: false)
                        .Annotation("Sqlite:Autoincrement", true),
                    QuietHoursStart = table.Column<TimeSpan>(type: "TEXT", nullable: false),
                    QuietHoursEnd = table.Column<TimeSpan>(type: "TEXT", nullable: false),
                    LowSensoryModeEnabled = table.Column<bool>(type: "INTEGER", nullable: false),
                    HighContrastEnabled = table.Column<bool>(type: "INTEGER", nullable: false),
                    ToastsEnabled = table.Column<bool>(type: "INTEGER", nullable: false),
                    UndoEnabled = table.Column<bool>(type: "INTEGER", nullable: false),
                    TimeZone = table.Column<string>(type: "TEXT", maxLength: 200, nullable: false),
                    FirstDayOfWeek = table.Column<int>(type: "INTEGER", nullable: false),
                    DailyBriefTime = table.Column<TimeSpan>(type: "TEXT", nullable: true),
                    CreatedAt = table.Column<DateTimeOffset>(type: "TEXT", nullable: false),
                    UpdatedAt = table.Column<DateTimeOffset>(type: "TEXT", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Settings", x => x.Id);
                });

            migrationBuilder.CreateTable(
                name: "HabitLogs",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "TEXT", nullable: false),
                    HabitId = table.Column<Guid>(type: "TEXT", nullable: false),
                    Date = table.Column<DateTime>(type: "TEXT", nullable: false),
                    Value = table.Column<double>(type: "REAL", nullable: true),
                    Note = table.Column<string>(type: "TEXT", maxLength: 2000, nullable: true),
                    CreatedAt = table.Column<DateTimeOffset>(type: "TEXT", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_HabitLogs", x => x.Id);
                    table.ForeignKey(
                        name: "FK_HabitLogs_Habits_HabitId",
                        column: x => x.HabitId,
                        principalTable: "Habits",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "Tasks",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "TEXT", nullable: false),
                    ProjectId = table.Column<Guid>(type: "TEXT", nullable: true),
                    Title = table.Column<string>(type: "TEXT", maxLength: 500, nullable: false),
                    Notes = table.Column<string>(type: "TEXT", maxLength: 4000, nullable: true),
                    DueAt = table.Column<DateTimeOffset>(type: "TEXT", nullable: true),
                    StartAt = table.Column<DateTimeOffset>(type: "TEXT", nullable: true),
                    CompletedAt = table.Column<DateTimeOffset>(type: "TEXT", nullable: true),
                    Priority = table.Column<int>(type: "INTEGER", nullable: false),
                    Status = table.Column<int>(type: "INTEGER", nullable: false),
                    EstimateMinutes = table.Column<int>(type: "INTEGER", nullable: true),
                    OrderIndex = table.Column<int>(type: "INTEGER", nullable: false, defaultValue: 0),
                    IsArchived = table.Column<bool>(type: "INTEGER", nullable: false, defaultValue: false),
                    CreatedAt = table.Column<DateTimeOffset>(type: "TEXT", nullable: false),
                    UpdatedAt = table.Column<DateTimeOffset>(type: "TEXT", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Tasks", x => x.Id);
                    table.ForeignKey(
                        name: "FK_Tasks_Projects_ProjectId",
                        column: x => x.ProjectId,
                        principalTable: "Projects",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.SetNull);
                });

            migrationBuilder.InsertData(
                table: "Settings",
                columns: new[] { "Id", "CreatedAt", "DailyBriefTime", "FirstDayOfWeek", "HighContrastEnabled", "LowSensoryModeEnabled", "QuietHoursEnd", "QuietHoursStart", "TimeZone", "ToastsEnabled", "UndoEnabled", "UpdatedAt" },
                values: new object[] { 1, new DateTimeOffset(new DateTime(2025, 10, 31, 17, 33, 40, 198, DateTimeKind.Unspecified).AddTicks(3631), new TimeSpan(0, 0, 0, 0, 0)), null, 1, false, false, new TimeSpan(0, 7, 0, 0, 0), new TimeSpan(0, 22, 0, 0, 0), "Mountain Standard Time", true, true, new DateTimeOffset(new DateTime(2025, 10, 31, 17, 33, 40, 198, DateTimeKind.Unspecified).AddTicks(3634), new TimeSpan(0, 0, 0, 0, 0)) });

            migrationBuilder.CreateIndex(
                name: "IX_Events_Start_End",
                table: "Events",
                columns: new[] { "Start", "End" });

            migrationBuilder.CreateIndex(
                name: "IX_HabitLogs_HabitId_Date",
                table: "HabitLogs",
                columns: new[] { "HabitId", "Date" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_Habits_Type_IsArchived",
                table: "Habits",
                columns: new[] { "Type", "IsArchived" });

            migrationBuilder.CreateIndex(
                name: "IX_Projects_Name",
                table: "Projects",
                column: "Name");

            migrationBuilder.CreateIndex(
                name: "IX_Routines_Enabled",
                table: "Routines",
                column: "Enabled");

            migrationBuilder.CreateIndex(
                name: "IX_Settings_FirstDayOfWeek",
                table: "Settings",
                column: "FirstDayOfWeek");

            migrationBuilder.CreateIndex(
                name: "IX_Tasks_DueAt",
                table: "Tasks",
                column: "DueAt");

            migrationBuilder.CreateIndex(
                name: "IX_Tasks_ProjectId",
                table: "Tasks",
                column: "ProjectId");

            migrationBuilder.CreateIndex(
                name: "IX_Tasks_Status_Priority",
                table: "Tasks",
                columns: new[] { "Status", "Priority" });
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "Events");

            migrationBuilder.DropTable(
                name: "HabitLogs");

            migrationBuilder.DropTable(
                name: "Routines");

            migrationBuilder.DropTable(
                name: "Settings");

            migrationBuilder.DropTable(
                name: "Tasks");

            migrationBuilder.DropTable(
                name: "Habits");

            migrationBuilder.DropTable(
                name: "Projects");
        }
    }
}
