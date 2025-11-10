using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace CalmCadence.Data.CalmCadence.Data.Migrations
{
    /// <inheritdoc />
    public partial class AddBriefCache : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.CreateTable(
                name: "BriefCache",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "TEXT", nullable: false),
                    Hash = table.Column<string>(type: "TEXT", nullable: false),
                    BriefJson = table.Column<string>(type: "TEXT", nullable: false),
                    CreatedAt = table.Column<DateTimeOffset>(type: "TEXT", nullable: false),
                    LastAccessedAt = table.Column<DateTimeOffset>(type: "TEXT", nullable: false),
                    AccessCount = table.Column<int>(type: "INTEGER", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_BriefCache", x => x.Id);
                });
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "BriefCache");
        }
    }
}
