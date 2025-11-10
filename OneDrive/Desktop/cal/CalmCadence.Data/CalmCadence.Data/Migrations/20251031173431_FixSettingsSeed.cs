using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace CalmCadence.Data.CalmCadence.Data.Migrations
{
    /// <inheritdoc />
    public partial class FixSettingsSeed : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.UpdateData(
                table: "Settings",
                keyColumn: "Id",
                keyValue: 1,
                columns: new[] { "CreatedAt", "TimeZone", "UpdatedAt" },
                values: new object[] { new DateTimeOffset(new DateTime(1970, 1, 1, 0, 0, 0, 0, DateTimeKind.Unspecified), new TimeSpan(0, 0, 0, 0, 0)), "UTC", new DateTimeOffset(new DateTime(1970, 1, 1, 0, 0, 0, 0, DateTimeKind.Unspecified), new TimeSpan(0, 0, 0, 0, 0)) });
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.UpdateData(
                table: "Settings",
                keyColumn: "Id",
                keyValue: 1,
                columns: new[] { "CreatedAt", "TimeZone", "UpdatedAt" },
                values: new object[] { new DateTimeOffset(new DateTime(2025, 10, 31, 17, 33, 40, 198, DateTimeKind.Unspecified).AddTicks(3631), new TimeSpan(0, 0, 0, 0, 0)), "Mountain Standard Time", new DateTimeOffset(new DateTime(2025, 10, 31, 17, 33, 40, 198, DateTimeKind.Unspecified).AddTicks(3634), new TimeSpan(0, 0, 0, 0, 0)) });
        }
    }
}
