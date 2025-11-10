using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace CalmCadence.Data.CalmCadence.Data.Migrations
{
    /// <inheritdoc />
    public partial class AddDailyStudio : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.AddColumn<bool>(
                name: "DailyStudioEnabled",
                table: "Settings",
                type: "INTEGER",
                nullable: false,
                defaultValue: false);

            migrationBuilder.AddColumn<bool>(
                name: "DailyStudioGenerateVideo",
                table: "Settings",
                type: "INTEGER",
                nullable: false,
                defaultValue: false);

            migrationBuilder.AddColumn<bool>(
                name: "DailyStudioIncludeCalendar",
                table: "Settings",
                type: "INTEGER",
                nullable: false,
                defaultValue: false);

            migrationBuilder.AddColumn<bool>(
                name: "DailyStudioIncludeHabits",
                table: "Settings",
                type: "INTEGER",
                nullable: false,
                defaultValue: false);

            migrationBuilder.AddColumn<bool>(
                name: "DailyStudioIncludeTasks",
                table: "Settings",
                type: "INTEGER",
                nullable: false,
                defaultValue: false);

            migrationBuilder.AddColumn<bool>(
                name: "DailyStudioOfflineFallback",
                table: "Settings",
                type: "INTEGER",
                nullable: false,
                defaultValue: false);

            migrationBuilder.AddColumn<string>(
                name: "DailyStudioPreferredMethod",
                table: "Settings",
                type: "TEXT",
                nullable: false,
                defaultValue: "");

            migrationBuilder.AddColumn<bool>(
                name: "DailyStudioRedactPrivateInfo",
                table: "Settings",
                type: "INTEGER",
                nullable: false,
                defaultValue: false);

            migrationBuilder.AddColumn<int>(
                name: "DailyStudioRetentionDays",
                table: "Settings",
                type: "INTEGER",
                nullable: false,
                defaultValue: 0);

            migrationBuilder.AddColumn<TimeSpan>(
                name: "DailyStudioTime",
                table: "Settings",
                type: "TEXT",
                nullable: false,
                defaultValue: new TimeSpan(0, 0, 0, 0, 0));

            migrationBuilder.AddColumn<string>(
                name: "DailyStudioTimeZone",
                table: "Settings",
                type: "TEXT",
                nullable: false,
                defaultValue: "");

            migrationBuilder.AddColumn<string>(
                name: "GeminiApiKey",
                table: "Settings",
                type: "TEXT",
                nullable: true);

            migrationBuilder.AddColumn<string>(
                name: "GoogleServiceAccountKeyPath",
                table: "Settings",
                type: "TEXT",
                nullable: true);

            migrationBuilder.CreateTable(
                name: "DailyMedia",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "TEXT", nullable: false),
                    Date = table.Column<DateTimeOffset>(type: "TEXT", nullable: false),
                    AudioFilePath = table.Column<string>(type: "TEXT", nullable: true),
                    VideoFilePath = table.Column<string>(type: "TEXT", nullable: true),
                    Title = table.Column<string>(type: "TEXT", nullable: true),
                    Description = table.Column<string>(type: "TEXT", nullable: true),
                    Duration = table.Column<TimeSpan>(type: "TEXT", nullable: true),
                    GenerationMethod = table.Column<string>(type: "TEXT", nullable: true),
                    ApiResponse = table.Column<string>(type: "TEXT", nullable: true),
                    IsFallbackUsed = table.Column<bool>(type: "INTEGER", nullable: false),
                    BriefJson = table.Column<string>(type: "TEXT", nullable: true),
                    BriefHash = table.Column<string>(type: "TEXT", nullable: true),
                    ExpiresAt = table.Column<DateTimeOffset>(type: "TEXT", nullable: false),
                    IsArchived = table.Column<bool>(type: "INTEGER", nullable: false),
                    CreatedAt = table.Column<DateTimeOffset>(type: "TEXT", nullable: false),
                    UpdatedAt = table.Column<DateTimeOffset>(type: "TEXT", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_DailyMedia", x => x.Id);
                });

            migrationBuilder.UpdateData(
                table: "Settings",
                keyColumn: "Id",
                keyValue: 1,
                columns: new[] { "DailyStudioEnabled", "DailyStudioGenerateVideo", "DailyStudioIncludeCalendar", "DailyStudioIncludeHabits", "DailyStudioIncludeTasks", "DailyStudioOfflineFallback", "DailyStudioPreferredMethod", "DailyStudioRedactPrivateInfo", "DailyStudioRetentionDays", "DailyStudioTime", "DailyStudioTimeZone", "GeminiApiKey", "GoogleServiceAccountKeyPath" },
                values: new object[] { true, true, true, true, true, true, "notebooklm", false, 30, new TimeSpan(0, 7, 30, 0, 0), "America/Denver", null, null });
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "DailyMedia");

            migrationBuilder.DropColumn(
                name: "DailyStudioEnabled",
                table: "Settings");

            migrationBuilder.DropColumn(
                name: "DailyStudioGenerateVideo",
                table: "Settings");

            migrationBuilder.DropColumn(
                name: "DailyStudioIncludeCalendar",
                table: "Settings");

            migrationBuilder.DropColumn(
                name: "DailyStudioIncludeHabits",
                table: "Settings");

            migrationBuilder.DropColumn(
                name: "DailyStudioIncludeTasks",
                table: "Settings");

            migrationBuilder.DropColumn(
                name: "DailyStudioOfflineFallback",
                table: "Settings");

            migrationBuilder.DropColumn(
                name: "DailyStudioPreferredMethod",
                table: "Settings");

            migrationBuilder.DropColumn(
                name: "DailyStudioRedactPrivateInfo",
                table: "Settings");

            migrationBuilder.DropColumn(
                name: "DailyStudioRetentionDays",
                table: "Settings");

            migrationBuilder.DropColumn(
                name: "DailyStudioTime",
                table: "Settings");

            migrationBuilder.DropColumn(
                name: "DailyStudioTimeZone",
                table: "Settings");

            migrationBuilder.DropColumn(
                name: "GeminiApiKey",
                table: "Settings");

            migrationBuilder.DropColumn(
                name: "GoogleServiceAccountKeyPath",
                table: "Settings");
        }
    }
}
